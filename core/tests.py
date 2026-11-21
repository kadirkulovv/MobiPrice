import asyncio
import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from django.core.cache import cache
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django.utils.translation import activate, gettext

from bot.handlers.client import (
    _confirm_login_token,
    _finalize_courier_order,
    cancel_courier_location,
    cmd_start_courier_deeplink,
    cmd_start_login_deeplink,
    process_courier_location,
    process_courier_location_without_state,
    process_login_phone_contact,
    prompt_location_again,
    reject_manual_login_phone,
    validate_verified_own_contact,
)
from bot.main import prune_empty_fsm_memory
from bot.states.client_states import CourierLocationStates, LoginAuthStates
from core.backup_service import create_db_backup, prune_old_backups
from core.distance import (
    HAVERSINE_ROAD_FACTOR,
    calculate_courier_fee_uzs,
    calculate_road_distance_km,
    haversine_distance_km,
)
from core.maintenance import (
    cleanup_excel_tmp,
    cleanup_expired_auth_tokens,
    cleanup_expired_sessions,
    cleanup_orphan_media,
    expire_stale_pending_courier_orders,
)
from core.models import (
    AuthToken,
    Brand,
    DeviceIssue,
    DevicePhone,
    DeviceSeries,
    IssueComparison,
    Review,
    ServiceOrder,
    TeamMember,
    TelegramUser,
)
from core.telegram_auth import (
    is_uzbek_phone_number,
    normalize_phone_number,
    normalize_uzbek_phone_number,
    sanitize_photo_url,
    upsert_telegram_user,
    verify_telegram_widget_data,
)

TEST_BOT_TOKEN = "123456789:TEST_SECRET_BOT_TOKEN_XYZ"
TEST_BOT_USERNAME = "MobiPriceTestBot"


def make_widget_payload(bot_token: str = TEST_BOT_TOKEN, **overrides) -> dict:
    payload = {
        'id': 777001122,
        'first_name': 'Ali',
        'last_name': 'Valiyev',
        'username': 'alivaliyev',
        'photo_url': 'https://t.me/i/userpic/320/alivaliyev.jpg',
        'auth_date': int(time.time()),
    }
    payload.update(overrides)
    check_parts = [
        f"{k}={payload[k]}"
        for k in sorted(payload.keys())
        if k != 'hash' and payload[k] not in (None, '')
    ]
    data_check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
    payload['hash'] = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return payload


def make_fake_bot_message(
    user_id: int = 555111222,
    first_name: str = "Sardor",
    last_name: str = "Karimov",
    username: str = "sardor_k",
    chat_type: str = "private",
    text: str = None,
    contact=None,
    location=None,
    forward_origin=None,
    forward_date=None,
    forward_from=None,
    forward_from_chat=None,
    forward_sender_name=None,
    is_automatic_forward=None,
    via_bot=None,
):
    msg = SimpleNamespace(
        chat=SimpleNamespace(id=user_id, type=chat_type),
        from_user=SimpleNamespace(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        ),
        text=text,
        contact=contact,
        location=location,
        forward_origin=forward_origin,
        forward_date=forward_date,
        forward_from=forward_from,
        forward_from_chat=forward_from_chat,
        forward_sender_name=forward_sender_name,
        is_automatic_forward=is_automatic_forward,
        via_bot=via_bot,
        answer=AsyncMock(),
    )
    return msg


def make_fsm_context(user_id: int = 555111222) -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(bot_id=999, chat_id=user_id, user_id=user_id)
    return FSMContext(storage=storage, key=key)


@override_settings(
    TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN,
    TELEGRAM_BOT_USERNAME=TEST_BOT_USERNAME,
    TELEGRAM_ADMIN_CHAT_ID="999000111",
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class TelegramWidgetAuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_verify_widget_valid_invalid_and_expired(self):
        valid_payload = make_widget_payload()
        ok, reason = verify_telegram_widget_data(valid_payload, TEST_BOT_TOKEN)
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")

        # Tampered field invalidates HMAC
        tampered = dict(valid_payload, first_name="Hacker")
        ok, reason = verify_telegram_widget_data(tampered, TEST_BOT_TOKEN)
        self.assertFalse(ok)
        self.assertIn("signature", reason.lower())

        # Wrong hash fails
        bad_hash = dict(valid_payload, hash="0" * 64)
        ok, _ = verify_telegram_widget_data(bad_hash, TEST_BOT_TOKEN)
        self.assertFalse(ok)

        # Expired auth_date fails
        expired = make_widget_payload(auth_date=int(time.time()) - 600)
        ok, reason = verify_telegram_widget_data(expired, TEST_BOT_TOKEN)
        self.assertFalse(ok)
        self.assertIn("expired", reason.lower())

        # Future auth_date fails
        future = make_widget_payload(auth_date=int(time.time()) + 300)
        ok, reason = verify_telegram_widget_data(future, TEST_BOT_TOKEN)
        self.assertFalse(ok)
        self.assertIn("future", reason.lower())

    def test_widget_endpoint_is_disabled_bot_only_auth(self):
        # Method 1 (Telegram Login Widget) is completely removed — bot-only verified +998 auth!
        res = self.client.post(
            '/api/auth/telegram/widget/',
            data=json.dumps(make_widget_payload(id=777001122)),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 404)

    def test_session_without_verified_uz_phone_is_rejected(self):
        # Empty phone user -> rejected
        no_phone_user = TelegramUser.objects.create(
            telegram_id=666111222,
            first_name="NoPhoneUser",
            phone_number="",
        )
        session = self.client.session
        session['telegram_user_id'] = no_phone_user.id
        session.save()

        me = self.client.get('/api/auth/me/').json()
        self.assertFalse(me['authenticated'])

        # Foreign non-+998 phone user -> rejected
        foreign_user = TelegramUser.objects.create(
            telegram_id=666111223,
            first_name="Foreign",
            phone_number="+79161234567",
        )
        session = self.client.session
        session['telegram_user_id'] = foreign_user.id
        session.save()

        me2 = self.client.get('/api/auth/me/').json()
        self.assertFalse(me2['authenticated'])

        # Verified Uzbekistan +998 user -> accepted!
        uz_user = TelegramUser.objects.create(
            telegram_id=666111224,
            first_name="UzClient",
            phone_number="+998902520703",
        )
        session = self.client.session
        session['telegram_user_id'] = uz_user.id
        session.save()

        me3 = self.client.get('/api/auth/me/').json()
        self.assertTrue(me3['authenticated'])
        self.assertEqual(me3['user']['phone_number'], '+998902520703')

    def test_sanitize_photo_url_blocks_bot_token_urls_and_upsert_preserves_phone(self):
        self.assertEqual(
            sanitize_photo_url(f"https://api.telegram.org/file/bot{TEST_BOT_TOKEN}/photos/1.jpg"),
            "",
        )
        self.assertEqual(
            sanitize_photo_url("https://t.me/i/userpic/320/demo.jpg"),
            "https://t.me/i/userpic/320/demo.jpg",
        )

        tg_user = upsert_telegram_user({
            'id': 888001,
            'first_name': 'Dilshod',
            'username': 'dilshod',
            'phone_number': '998902520703',
        })
        self.assertEqual(tg_user.phone_number, '+998902520703')

        # Subsequent widget upsert without phone_number must preserve verified phone_number
        tg_user_updated = upsert_telegram_user({
            'id': 888001,
            'first_name': 'Dilshodjon',
            'username': 'dilshod',
        })
        self.assertEqual(tg_user_updated.first_name, 'Dilshodjon')
        self.assertEqual(tg_user_updated.phone_number, '+998902520703')


@override_settings(
    TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN,
    TELEGRAM_BOT_USERNAME=TEST_BOT_USERNAME,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class TelegramBotDeepLinkAndPhoneVerificationTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_phone_normalization_and_uzbekistan_only_rule(self):
        self.assertEqual(normalize_phone_number('998902520703'), '+998902520703')
        self.assertEqual(normalize_phone_number('+998 (90) 252-07-03'), '+998902520703')
        self.assertEqual(normalize_phone_number('123'), '')
        self.assertEqual(normalize_phone_number(''), '')

        # Uzbekistan (+998 + 9 digits) accepted
        self.assertTrue(is_uzbek_phone_number('+998902520703'))
        self.assertTrue(is_uzbek_phone_number('998949980703'))
        self.assertEqual(normalize_uzbek_phone_number('+998 (77) 123-45-67'), '+998771234567')

        # Non-Uzbekistan / invalid length numbers MUST be rejected
        for foreign in ('+79161234567', '+14155552671', '+88801234567', '+992901234567', '+99812345', '+9989012345678'):
            self.assertFalse(is_uzbek_phone_number(foreign), f"Should reject {foreign}")
            self.assertEqual(normalize_uzbek_phone_number(foreign), '')

    def test_foreign_phone_number_is_rejected_in_bot_login_flow(self):
        # Bot deep-link flow with Russian (+7) Telegram account -> REJECTED!
        start_res = self.client.post('/api/auth/telegram/deeplink/start/')
        token = start_res.json()['token']

        state = make_fsm_context(user_id=777111000)
        start_msg = make_fake_bot_message(user_id=777111000, text=f"/start login_{token}")
        asyncio.run(cmd_start_login_deeplink(start_msg, SimpleNamespace(args=f"login_{token}"), state))
        self.assertEqual(asyncio.run(state.get_state()), LoginAuthStates.waiting_for_phone.state)

        ru_contact = SimpleNamespace(
            phone_number="+79161234567",
            first_name="Ivan",
            last_name="",
            user_id=777111000,
            vcard=None,
        )
        ru_msg = make_fake_bot_message(user_id=777111000, contact=ru_contact)
        asyncio.run(process_login_phone_contact(ru_msg, state))

        # State cleared, token marked rejected, polling returns 403 rejected!
        self.assertIsNone(asyncio.run(state.get_state()))
        self.assertIn("+998", ru_msg.answer.call_args.args[0])
        auth_token = AuthToken.objects.get(token=token)
        self.assertFalse(auth_token.is_confirmed)
        self.assertEqual(auth_token.rejected_reason, 'non_uz_phone')

        poll_rej = self.client.get(f'/api/auth/telegram/deeplink/status/?token={token}&lang=uz')
        self.assertEqual(poll_rej.status_code, 403)
        self.assertEqual(poll_rej.json()['status'], 'rejected')
        self.assertEqual(poll_rej.json()['reason'], 'non_uz_phone')
        self.assertFalse(poll_rej.json()['authenticated'])

    def test_bot_login_requires_verified_reply_keyboard_contact_and_rejects_spoofs(self):
        # 1. Start deep-link auth from browser
        start_res = self.client.post(
            '/api/auth/telegram/deeplink/start/',
            data=json.dumps({'lang': 'uz'}),
            content_type='application/json',
        )
        self.assertEqual(start_res.status_code, 200)
        start_data = start_res.json()
        token = start_data['token']
        self.assertTrue(start_data['bot_url'].startswith(f"https://t.me/{TEST_BOT_USERNAME}?start=login_"))
        self.assertLessEqual(len(f"login_{token}"), 64)

        # Polling before bot start -> pending
        poll1 = self.client.get(f'/api/auth/telegram/deeplink/status/?token={token}').json()
        self.assertEqual(poll1['status'], 'pending')
        self.assertFalse(poll1['authenticated'])

        # 2. User sends /start login_<token> to bot
        state = make_fsm_context(user_id=555111222)
        start_msg = make_fake_bot_message(user_id=555111222, text=f"/start login_{token}")
        command = SimpleNamespace(args=f"login_{token}")

        asyncio.run(cmd_start_login_deeplink(start_msg, command, state))

        # Must enter waiting_for_phone state and send request_contact=True ReplyKeyboardMarkup
        self.assertEqual(asyncio.run(state.get_state()), LoginAuthStates.waiting_for_phone.state)
        self.assertTrue(start_msg.answer.called)
        kb = start_msg.answer.call_args.kwargs.get('reply_markup')
        self.assertIsInstance(kb, ReplyKeyboardMarkup)
        self.assertTrue(kb.keyboard[0][0].request_contact)

        # Token MUST still be unconfirmed before button press!
        auth_token_obj = AuthToken.objects.get(token=token)
        self.assertFalse(auth_token_obj.is_confirmed)

        # 3. Attack A: Manual text input (+998902520703) -> MUST BE REJECTED
        manual_msg = make_fake_bot_message(user_id=555111222, text="+998902520703")
        asyncio.run(reject_manual_login_phone(manual_msg, state))
        auth_token_obj.refresh_from_db()
        self.assertFalse(auth_token_obj.is_confirmed)
        self.assertEqual(asyncio.run(state.get_state()), LoginAuthStates.waiting_for_phone.state)
        self.assertIn("qabul qilinmaydi", manual_msg.answer.call_args.args[0].lower())

        # 4. Attack B: Sharing ANOTHER person's contact (different user_id) -> MUST BE REJECTED
        other_contact = SimpleNamespace(
            phone_number="+998901112233",
            first_name="Other",
            last_name="",
            user_id=999888777,
            vcard=None,
        )
        other_msg = make_fake_bot_message(user_id=555111222, contact=other_contact)
        asyncio.run(process_login_phone_contact(other_msg, state))
        auth_token_obj.refresh_from_db()
        self.assertFalse(auth_token_obj.is_confirmed)
        self.assertEqual(asyncio.run(state.get_state()), LoginAuthStates.waiting_for_phone.state)
        self.assertIn("boshqa odam", other_msg.answer.call_args.args[0].lower())

        # 5. Attack C: Sharing unregistered contact (user_id=None) -> MUST BE REJECTED
        unreg_contact = SimpleNamespace(
            phone_number="+998902520703",
            first_name="Fake",
            last_name="",
            user_id=None,
            vcard=None,
        )
        unreg_msg = make_fake_bot_message(user_id=555111222, contact=unreg_contact)
        asyncio.run(process_login_phone_contact(unreg_msg, state))
        auth_token_obj.refresh_from_db()
        self.assertFalse(auth_token_obj.is_confirmed)

        # 6. Attack D: Sharing contact via address book with vCard -> MUST BE REJECTED
        vcard_contact = SimpleNamespace(
            phone_number="+998902520703",
            first_name="Sardor",
            last_name="Karimov",
            user_id=555111222,
            vcard="BEGIN:VCARD\nVERSION:3.0\nTEL:+998902520703\nEND:VCARD",
        )
        vcard_msg = make_fake_bot_message(user_id=555111222, contact=vcard_contact)
        asyncio.run(process_login_phone_contact(vcard_msg, state))
        auth_token_obj.refresh_from_db()
        self.assertFalse(auth_token_obj.is_confirmed)
        self.assertIn("share contact", vcard_msg.answer.call_args.args[0].lower())

        # 7. Attack E: Forwarding a contact message -> MUST BE REJECTED
        fwd_contact = SimpleNamespace(
            phone_number="+998902520703",
            first_name="Sardor",
            last_name="Karimov",
            user_id=555111222,
            vcard=None,
        )
        fwd_msg = make_fake_bot_message(
            user_id=555111222,
            contact=fwd_contact,
            forward_date=int(time.time()),
            forward_origin=SimpleNamespace(type="user"),
        )
        asyncio.run(process_login_phone_contact(fwd_msg, state))
        auth_token_obj.refresh_from_db()
        self.assertFalse(auth_token_obj.is_confirmed)
        self.assertIn("forward", fwd_msg.answer.call_args.args[0].lower())

        # 8. Defense in depth: _confirm_login_token without phone_number MUST fail
        ok_no_phone, st_no_phone = _confirm_login_token(token, {'id': 555111222, 'first_name': 'Sardor'})
        self.assertFalse(ok_no_phone)
        self.assertEqual(st_no_phone, 'phone_required')

        # 9. Legitimate ReplyKeyboard button press (own Telegram account, no vcard, no forward) -> ACCEPTED!
        real_contact = SimpleNamespace(
            phone_number="998902520703",
            first_name="Sardor",
            last_name="Karimov",
            user_id=555111222,
            vcard=None,
        )
        real_msg = make_fake_bot_message(user_id=555111222, contact=real_contact)
        valid_flag, valid_reason, norm_phone = validate_verified_own_contact(real_msg)
        self.assertTrue(valid_flag)
        self.assertEqual(valid_reason, "ok")
        self.assertEqual(norm_phone, "+998902520703")

        asyncio.run(process_login_phone_contact(real_msg, state))

        auth_token_obj.refresh_from_db()
        self.assertTrue(auth_token_obj.is_confirmed)
        self.assertIsNotNone(auth_token_obj.telegram_user)
        self.assertEqual(auth_token_obj.telegram_user.phone_number, "+998902520703")
        self.assertIsNone(asyncio.run(state.get_state()))
        self.assertIsInstance(real_msg.answer.call_args.kwargs.get('reply_markup'), ReplyKeyboardRemove)

        # 10. Different browser session MUST NOT consume this token
        other_browser = Client()
        other_browser.get('/api/auth/me/')
        steal_res = other_browser.get(f'/api/auth/telegram/deeplink/status/?token={token}')
        self.assertIn(steal_res.status_code, (403, 404))

        # 11. Original browser polls and logs in atomically (one-time use)
        poll_ok = self.client.get(f'/api/auth/telegram/deeplink/status/?token={token}')
        self.assertEqual(poll_ok.status_code, 200)
        poll_data = poll_ok.json()
        self.assertEqual(poll_data['status'], 'confirmed')
        self.assertTrue(poll_data['authenticated'])
        self.assertEqual(poll_data['user']['phone_number'], '+998902520703')

        # 12. Token is marked used and cannot be replayed (cycle_key + is_used=True)
        auth_token_obj.refresh_from_db()
        self.assertTrue(auth_token_obj.is_used)
        poll_reuse = self.client.get(f'/api/auth/telegram/deeplink/status/?token={token}')
        self.assertIn(poll_reuse.status_code, (404, 410))
        self.assertFalse(poll_reuse.json()['authenticated'])

        # Bot also rejects reusing the already-used token
        reuse_state = make_fsm_context(user_id=555111222)
        reuse_msg = make_fake_bot_message(user_id=555111222, text=f"/start login_{token}")
        asyncio.run(cmd_start_login_deeplink(reuse_msg, SimpleNamespace(args=f"login_{token}"), reuse_state))
        self.assertIsNone(asyncio.run(reuse_state.get_state()))
        self.assertIn("ishlatilgan", reuse_msg.answer.call_args.args[0].lower())

        # 13. Logout clears session
        logout_res = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_res.status_code, 200)
        self.assertFalse(self.client.get('/api/auth/me/').json()['authenticated'])

    def test_expired_deeplink_token(self):
        start_res = self.client.post('/api/auth/telegram/deeplink/start/')
        token = start_res.json()['token']
        AuthToken.objects.filter(token=token).update(expires_at=timezone.now() - timedelta(minutes=1))

        poll_res = self.client.get(f'/api/auth/telegram/deeplink/status/?token={token}')
        self.assertEqual(poll_res.status_code, 200)
        self.assertEqual(poll_res.json()['status'], 'expired')

        # Bot also rejects expired link without entering waiting state
        state = make_fsm_context(user_id=444333222)
        msg = make_fake_bot_message(user_id=444333222, text=f"/start login_{token}")
        asyncio.run(cmd_start_login_deeplink(msg, SimpleNamespace(args=f"login_{token}"), state))
        self.assertIsNone(asyncio.run(state.get_state()))
        self.assertIn("muddati o'tgan", msg.answer.call_args.args[0].lower())


@override_settings(
    TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN,
    TELEGRAM_BOT_USERNAME=TEST_BOT_USERNAME,
    TELEGRAM_ADMIN_CHAT_ID="999000111",
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class OrdersReviewsAndCourierTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.brand = Brand.objects.create(name="Apple", order=1)
        self.series = DeviceSeries.objects.create(brand=self.brand, name="iPhone 15", order=1)
        self.phone = DevicePhone.objects.create(series=self.series, name="iPhone 15 Pro", order=1)
        self.issue = DeviceIssue.objects.create(phone=self.phone, title="Ekran almashtirish", icon_number=1)
        self.comp = IssueComparison.objects.create(
            issue=self.issue,
            quality_type='original_service_pack',
            title="Original Service Pack",
            part_price_uzs=Decimal("1000000"),
            service_fee_uzs=Decimal("200000"),
            price_usd=Decimal("95"),
        )

    def _login_user(self, telegram_id=123456789, phone_number='+998902520703'):
        tg_user = TelegramUser.objects.create(
            telegram_id=telegram_id,
            first_name="Murodjon",
            last_name="Test",
            username="murodjon_test",
            phone_number=phone_number,
        )
        session = self.client.session
        session['telegram_user_id'] = tg_user.id
        session.save()
        return tg_user

    def test_unauthenticated_order_and_review_return_401(self):
        order_res = self.client.post(
            '/api/orders/submit/',
            data=json.dumps({
                'phone_id': self.phone.id,
                'comparison_id': self.comp.id,
                'service_type': 'in_service',
            }),
            content_type='application/json',
        )
        self.assertEqual(order_res.status_code, 401)
        self.assertTrue(order_res.json()['auth_required'])

        review_res = self.client.post(
            '/api/reviews/submit/',
            data=json.dumps({
                'device_model': 'iPhone 15 Pro',
                'service_type': 'Ekran',
                'rating': 5,
                'comment': 'Zo‘r servis!',
            }),
            content_type='application/json',
        )
        self.assertEqual(review_res.status_code, 401)
        self.assertTrue(review_res.json()['auth_required'])

    def test_review_uses_session_user_and_enforces_24h_limit(self):
        tg_user = self._login_user()
        with patch('core.views._send_telegram_notifications_async'):
            res1 = self.client.post(
                '/api/reviews/submit/',
                data=json.dumps({
                    'client_name': 'Spoofed Name',
                    'device_model': 'iPhone 15 Pro',
                    'service_type': 'Ekran',
                    'rating': 5,
                    'comment': 'Juda tez va sifatli!',
                    'device_fingerprint': 'fp_test_1',
                }),
                content_type='application/json',
            )
            self.assertEqual(res1.status_code, 200)
            self.assertEqual(res1.json()['review']['client_name'], tg_user.full_name)
            self.assertEqual(Review.objects.get().telegram_user_id, tg_user.id)

            res2 = self.client.post(
                '/api/reviews/submit/',
                data=json.dumps({
                    'device_model': 'iPhone 15 Pro',
                    'service_type': 'Batareya',
                    'rating': 5,
                    'comment': 'Yana bitta sharh',
                    'device_fingerprint': 'fp_test_2',
                }),
                content_type='application/json',
            )
            self.assertEqual(res2.status_code, 429)

    def test_call_master_is_rejected(self):
        self._login_user()
        res = self.client.post(
            '/api/orders/submit/',
            data=json.dumps({
                'phone_id': self.phone.id,
                'comparison_id': self.comp.id,
                'service_type': 'call_master',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])

    def test_unverified_phone_user_cannot_place_order_and_spoofed_json_phone_ignored(self):
        # User without verified +998 phone cannot place an order (401)
        self._login_user(telegram_id=333444555, phone_number='')
        res_unverified = self.client.post(
            '/api/orders/submit/',
            data=json.dumps({
                'phone_id': self.phone.id,
                'comparison_id': self.comp.id,
                'service_type': 'in_service',
                'phone_number': '+998901112233',  # spoofed manual phone must NOT bypass auth!
                'lang': 'uz',
            }),
            content_type='application/json',
        )
        self.assertEqual(res_unverified.status_code, 401)
        self.assertTrue(res_unverified.json().get('auth_required'))

        # Verified +998 user always uses their bot-verified phone, ignoring manual JSON phone
        self._login_user(telegram_id=333444556, phone_number='+998902520703')
        with patch('core.views._send_telegram_notifications_async'):
            res_ok = self.client.post(
                '/api/orders/submit/',
                data=json.dumps({
                    'phone_id': self.phone.id,
                    'comparison_id': self.comp.id,
                    'service_type': 'in_service',
                    'phone_number': '+998999999999',
                    'lang': 'uz',
                }),
                content_type='application/json',
            )
            self.assertEqual(res_ok.status_code, 200)
            self.assertEqual(res_ok.json()['phone_number'], '+998902520703')
            order = ServiceOrder.objects.get(order_id=res_ok.json()['order_id'])
            self.assertEqual(order.phone_number, '+998902520703')

    def test_in_service_order_returns_shop_location_and_saves_verified_phone(self):
        self._login_user(phone_number='+998902520703')
        with patch('core.views._send_telegram_notifications_async') as mock_notify:
            res = self.client.post(
                '/api/orders/submit/',
                data=json.dumps({
                    'phone_id': self.phone.id,
                    'comparison_id': self.comp.id,
                    'service_type': 'in_service',
                    'lang': 'uz',
                }),
                content_type='application/json',
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['service_type'], 'in_service')
            loc = data['shop_location']
            self.assertEqual(loc['address'], "Malika bozor, B32 do'kon")
            self.assertIn('41.338306,69.270389', loc['google_maps_url'])
            self.assertIn('pt=69.270389,41.338306', loc['yandex_maps_url'])

            order = ServiceOrder.objects.get(order_id=data['order_id'])
            self.assertEqual(order.status, 'new')
            self.assertEqual(order.phone_number, '+998902520703')
            self.assertEqual(order.final_total_uzs, Decimal('1200000'))

            # Admin notification must include the verified phone number
            self.assertTrue(mock_notify.called)
            sent_text = mock_notify.call_args.kwargs['payload_base']['text']
            self.assertIn('+998902520703', sent_text)

    def test_my_orders_requires_login_isolates_accounts_and_paginates_by_10(self):
        # 1. Unauthenticated requests MUST return 401
        res_unauth_my = self.client.get('/api/orders/my/')
        self.assertEqual(res_unauth_my.status_code, 401)
        self.assertTrue(res_unauth_my.json().get('auth_required'))

        res_unauth_track = self.client.get('/api/orders/track/?order_id=MP-ABCDEF')
        self.assertEqual(res_unauth_track.status_code, 401)
        self.assertTrue(res_unauth_track.json().get('auth_required'))

        # 2. Create 23 orders for User A and 3 orders for User B
        user_a = self._login_user(telegram_id=101010101, phone_number='+998902520703')
        user_b = TelegramUser.objects.create(
            telegram_id=202020202,
            first_name="Boshqa",
            username="boshqa_user",
            phone_number="+998901112233",
        )

        user_a_order_ids = []
        for idx in range(23):
            o = ServiceOrder.objects.create(
                telegram_user=user_a,
                client_name=user_a.full_name,
                phone_number=user_a.phone_number,
                phone=self.phone,
                comparison=self.comp,
                service_type='in_service',
                status='new',
                final_total_uzs=self.comp.total_price_uzs,
            )
            user_a_order_ids.append(o.order_id)

        user_b_orders = []
        for idx in range(3):
            ob = ServiceOrder.objects.create(
                telegram_user=user_b,
                client_name=user_b.full_name,
                phone_number=user_b.phone_number,
                phone=self.phone,
                comparison=self.comp,
                service_type='in_service',
                status='new',
                final_total_uzs=self.comp.total_price_uzs,
            )
            user_b_orders.append(ob.order_id)

        # 3. IDOR check: User A cannot inspect User B's order via /api/orders/track/
        idor_res = self.client.get(f'/api/orders/track/?order_id={user_b_orders[0]}&lang=uz')
        self.assertEqual(idor_res.status_code, 404)

        # 4. Page 1: 10 items, newest first, total_count=23, total_pages=3
        p1 = self.client.get('/api/orders/my/?page=1&lang=uz').json()
        self.assertTrue(p1['success'])
        self.assertEqual(p1['total_count'], 23)
        self.assertEqual(p1['per_page'], 10)
        self.assertEqual(p1['total_pages'], 3)
        self.assertEqual(p1['page'], 1)
        self.assertFalse(p1['has_previous'])
        self.assertTrue(p1['has_next'])
        self.assertEqual(p1['next_page'], 2)
        self.assertEqual(len(p1['orders']), 10)
        p1_ids = [item['order_id'] for item in p1['orders']]
        self.assertEqual(p1_ids[0], user_a_order_ids[-1])  # newest first

        # 5. Page 2: next 10 items, disjoint from Page 1
        p2 = self.client.get('/api/orders/my/?page=2&lang=uz').json()
        self.assertEqual(p2['page'], 2)
        self.assertTrue(p2['has_previous'])
        self.assertEqual(p2['previous_page'], 1)
        self.assertTrue(p2['has_next'])
        self.assertEqual(p2['next_page'], 3)
        self.assertEqual(len(p2['orders']), 10)
        p2_ids = [item['order_id'] for item in p2['orders']]
        self.assertEqual(len(set(p1_ids) & set(p2_ids)), 0)

        # 6. Page 3: remaining 3 items, none from User B
        p3 = self.client.get('/api/orders/my/?page=3&lang=uz').json()
        self.assertEqual(p3['page'], 3)
        self.assertTrue(p3['has_previous'])
        self.assertEqual(p3['previous_page'], 2)
        self.assertFalse(p3['has_next'])
        self.assertIsNone(p3['next_page'])
        self.assertEqual(len(p3['orders']), 3)
        p3_ids = [item['order_id'] for item in p3['orders']]

        all_returned = set(p1_ids + p2_ids + p3_ids)
        self.assertEqual(all_returned, set(user_a_order_ids))
        self.assertEqual(len(all_returned & set(user_b_orders)), 0)

        # 7. Out-of-range / invalid page param clamps safely
        p_invalid = self.client.get('/api/orders/my/?page=abc&lang=uz').json()
        self.assertEqual(p_invalid['page'], 1)
        p_overflow = self.client.get('/api/orders/my/?page=999&lang=uz').json()
        self.assertEqual(p_overflow['page'], 3)

    def test_courier_order_distance_formula_osrm_and_haversine_fallback(self):
        # Fee formula check: 2.5 km -> 5000 + 25000 = 30 000 so'm
        self.assertEqual(calculate_courier_fee_uzs(2.5), 30000)
        self.assertEqual(calculate_courier_fee_uzs(0), 5000)

        # OSRM success path
        fake_resp = MagicMock(status_code=200)
        fake_resp.json.return_value = {'routes': [{'distance': 2500.0}]}
        with patch('core.distance.requests.get', return_value=fake_resp):
            km, source = calculate_road_distance_km(41.3500, 69.2800)
            self.assertEqual(km, 2.5)
            self.assertEqual(source, 'osrm')

        # Haversine * 1.25 fallback path
        with patch('core.distance.requests.get', side_effect=RuntimeError("network down")):
            km_fb, source_fb = calculate_road_distance_km(41.3500, 69.2800)
            expected = round(
                haversine_distance_km(41.338306, 69.270389, 41.3500, 69.2800) * HAVERSINE_ROAD_FACTOR,
                2,
            )
            self.assertEqual(source_fb, 'haversine')
            self.assertEqual(km_fb, expected)

        # Full courier order creation -> pending_location -> finalize -> track
        tg_user = self._login_user(telegram_id=987654321, phone_number='+998902520703')
        res = self.client.post(
            '/api/orders/submit/',
            data=json.dumps({
                'phone_id': self.phone.id,
                'comparison_id': self.comp.id,
                'service_type': 'courier',
                'lang': 'uz',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['service_type'], 'courier')
        self.assertEqual(body['status'], 'pending_location')
        self.assertIn(f"https://t.me/{TEST_BOT_USERNAME}?start=courier_", body['bot_url'])

        order = ServiceOrder.objects.get(order_id=body['order_id'])
        self.assertEqual(order.status, 'pending_location')
        self.assertEqual(order.phone_number, '+998902520703')
        self.assertLessEqual(len(f"courier_{order.courier_token}"), 64)

        # Track before location
        track_pending = self.client.get(f'/api/orders/track/?order_id={order.order_id}&lang=uz').json()
        self.assertTrue(track_pending['found'])
        self.assertEqual(track_pending['status'], 'pending_location')
        self.assertNotIn('phone_number', track_pending)

        # Finalize courier order with 2.5 km -> 30 000 so'm fee -> final_total = 1 230 000 so'm
        fin_status, fin_result = _finalize_courier_order(
            order_pk=order.id,
            token_value=order.courier_token,
            telegram_id=tg_user.telegram_id,
            lat=41.3500,
            lon=69.2800,
            distance_km=2.5,
            delivery_fee_uzs=calculate_courier_fee_uzs(2.5),
        )
        self.assertEqual(fin_status, 'ok')
        self.assertEqual(fin_result['delivery_fee_uzs'], 30000)
        self.assertEqual(fin_result['final_total_uzs'], 1230000)
        self.assertEqual(fin_result['phone_number'], '+998902520703')

        order.refresh_from_db()
        self.assertEqual(order.status, 'new')
        self.assertIsNone(order.courier_token)
        self.assertEqual(order.distance_km, Decimal('2.50'))
        self.assertEqual(order.delivery_fee_uzs, Decimal('30000'))
        self.assertEqual(order.final_total_uzs, Decimal('1230000'))

        # Track after location
        track_done = self.client.get(f'/api/orders/track/?order_id={order.order_id}&lang=uz').json()
        self.assertEqual(track_done['status'], 'new')
        self.assertEqual(track_done['final_total_uzs'], 1230000)
        self.assertEqual(track_done['delivery_fee_uzs'], 30000)


class I18nAndTemplatesTests(TestCase):
    def test_compiled_translations_load_for_uz_ru_en(self):
        activate('ru')
        self.assertEqual(gettext("Telegram orqali kirish"), "Войти через Telegram")
        self.assertEqual(gettext("Chiqish"), "Выйти")

        activate('en')
        self.assertEqual(gettext("Telegram orqali kirish"), "Sign in with Telegram")
        self.assertEqual(gettext("Buyurtmangiz qabul qilindi!"), "Order confirmed!")

        activate('uz')
        self.assertEqual(gettext("Telegram orqali kirish"), "Telegram orqali kirish")

    def test_pages_render_bot_only_auth_without_inline_styles_or_widget(self):
        client = Client()
        for lang_code in ('uz', 'ru', 'en'):
            resp = client.get(f'/{lang_code}/')
            self.assertEqual(resp.status_code, 200)
            html_content = resp.content.decode('utf-8')
            self.assertIn('auth_modal.css?v=7', html_content)
            self.assertIn('auth.js?v=10', html_content)
            self.assertIn('track.js?v=11', html_content)
            self.assertIn('track_modal.css?v=11', html_content)
            self.assertIn('modal.js?v=8', html_content)
            self.assertIn('id="btn-auth-deeplink"', html_content)
            self.assertIn('id="my-orders-pagination"', html_content)
            self.assertNotIn('id="track-order-input"', html_content)
            self.assertNotIn('telegram-widget.js', html_content)
            self.assertNotIn('onTelegramAuth', html_content)
            self.assertNotIn('order-phone-input', html_content)
            self.assertNotIn('style="', html_content)
            self.assertNotIn('<style', html_content)
            self.assertNotIn('lang-pills', html_content)


@override_settings(
    TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN,
    TELEGRAM_BOT_USERNAME=TEST_BOT_USERNAME,
    TELEGRAM_ADMIN_CHAT_ID="999000111",
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class CourierLifecycleAndTimeoutTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.brand = Brand.objects.create(name="Apple", order=1)
        self.series = DeviceSeries.objects.create(brand=self.brand, name="iPhone 16", order=1)
        self.phone = DevicePhone.objects.create(series=self.series, name="iPhone 16 Pro Max", order=1)
        self.issue = DeviceIssue.objects.create(phone=self.phone, title="Batareya almashtirish", icon_number=2)
        self.comp = IssueComparison.objects.create(
            issue=self.issue,
            quality_type='original_service_pack',
            title="Original Service Pack",
            part_price_uzs=Decimal("800000"),
            service_fee_uzs=Decimal("0"),
            price_usd=Decimal("62"),
        )
        self.tg_user = TelegramUser.objects.create(
            telegram_id=555888111,
            first_name="Javohir",
            username="javohir_client",
            phone_number="+998949980703",
        )
        session = self.client.session
        session['telegram_user_id'] = self.tg_user.id
        session.save()

    def _create_courier_order(self):
        res = self.client.post(
            '/api/orders/submit/',
            data=json.dumps({
                'phone_id': self.phone.id,
                'comparison_id': self.comp.id,
                'service_type': 'courier',
                'lang': 'uz',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        order = ServiceOrder.objects.get(order_id=body['order_id'])
        return order, body

    def test_cancel_in_bot_auto_cancels_order_in_db_and_website(self):
        order, _ = self._create_courier_order()
        state = make_fsm_context(user_id=self.tg_user.telegram_id)

        # User opens deep link in bot
        start_msg = make_fake_bot_message(user_id=self.tg_user.telegram_id, text=f"/start courier_{order.courier_token}")
        asyncio.run(cmd_start_courier_deeplink(start_msg, SimpleNamespace(args=f"courier_{order.courier_token}"), state))
        self.assertEqual(asyncio.run(state.get_state()), CourierLocationStates.waiting_for_location.state)

        # User clicks Cancel without sending location -> DB order MUST become cancelled immediately
        cancel_msg = make_fake_bot_message(user_id=self.tg_user.telegram_id, text="❌ Bekor qilish")
        asyncio.run(cancel_courier_location(cancel_msg, state))

        self.assertIsNone(asyncio.run(state.get_state()))
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertIsNone(order.courier_token)

        # Website API immediately reflects cancelled status with no bot_url
        my_orders = self.client.get('/api/orders/my/?page=1&lang=uz').json()
        self.assertEqual(my_orders['orders'][0]['order_id'], order.order_id)
        self.assertEqual(my_orders['orders'][0]['status'], 'cancelled')
        self.assertEqual(my_orders['orders'][0]['bot_url'], '')

    def test_repeatable_website_button_recovers_after_accidental_message_or_state_switch(self):
        order, body = self._create_courier_order()
        token = order.courier_token
        state = make_fsm_context(user_id=self.tg_user.telegram_id)

        # 1st click on website button -> enters waiting_for_location
        msg1 = make_fake_bot_message(user_id=self.tg_user.telegram_id, text=f"/start courier_{token}")
        asyncio.run(cmd_start_courier_deeplink(msg1, SimpleNamespace(args=f"courier_{token}"), state))
        self.assertEqual(asyncio.run(state.get_state()), CourierLocationStates.waiting_for_location.state)

        # User accidentally sends random text -> stays in waiting_for_location and reminds order ID
        junk_msg = make_fake_bot_message(user_id=self.tg_user.telegram_id, text="salom nima gap")
        asyncio.run(prompt_location_again(junk_msg, state))
        self.assertEqual(asyncio.run(state.get_state()), CourierLocationStates.waiting_for_location.state)
        self.assertIn(order.order_id, junk_msg.answer.call_args.args[0])

        # User accidentally switches FSM state to another unrelated state
        asyncio.run(state.set_state(LoginAuthStates.waiting_for_phone))
        self.assertEqual(asyncio.run(state.get_state()), LoginAuthStates.waiting_for_phone.state)

        # Website STILL shows the persistent bot_url button (does NOT disappear after 1st click!)
        my_orders = self.client.get('/api/orders/my/?page=1&lang=uz').json()
        card = my_orders['orders'][0]
        self.assertEqual(card['status'], 'pending_location')
        self.assertEqual(card['bot_url'], body['bot_url'])
        self.assertGreater(card['location_remaining_seconds'], 0)

        # 2nd click on the SAME website button -> recovers exact same order and resets state back!
        msg2 = make_fake_bot_message(user_id=self.tg_user.telegram_id, text=f"/start courier_{token}")
        asyncio.run(cmd_start_courier_deeplink(msg2, SimpleNamespace(args=f"courier_{token}"), state))
        self.assertEqual(asyncio.run(state.get_state()), CourierLocationStates.waiting_for_location.state)
        state_data = asyncio.run(state.get_data())
        self.assertEqual(state_data['courier_order_pk'], order.id)
        self.assertEqual(state_data['courier_order_id'], order.order_id)

        # Now user sends location -> order finalizes to 'new' and button disappears only AFTER completion
        fake_bot = SimpleNamespace(send_message=AsyncMock(), send_location=AsyncMock())
        loc_msg = make_fake_bot_message(
            user_id=self.tg_user.telegram_id,
            location=SimpleNamespace(latitude=41.3500, longitude=69.2800),
        )
        with patch('bot.handlers.client.calculate_road_distance_km', return_value=(2.5, 'osrm')):
            asyncio.run(process_courier_location(loc_msg, state, fake_bot))

        order.refresh_from_db()
        self.assertEqual(order.status, 'new')
        self.assertIsNone(order.courier_token)
        self.assertEqual(order.delivery_fee_uzs, Decimal('30000'))

    def test_location_without_fsm_state_fallback_for_single_active_order(self):
        order, _ = self._create_courier_order()
        # Simulate bot restart where FSM state is None
        empty_state = make_fsm_context(user_id=self.tg_user.telegram_id)
        fake_bot = SimpleNamespace(send_message=AsyncMock(), send_location=AsyncMock())
        loc_msg = make_fake_bot_message(
            user_id=self.tg_user.telegram_id,
            location=SimpleNamespace(latitude=41.3500, longitude=69.2800),
        )
        with patch('bot.handlers.client.calculate_road_distance_km', return_value=(1.5, 'osrm')):
            asyncio.run(process_courier_location_without_state(loc_msg, empty_state, fake_bot))

        order.refresh_from_db()
        self.assertEqual(order.status, 'new')
        self.assertEqual(order.delivery_fee_uzs, Decimal('20000'))

    def test_pending_courier_order_auto_cancels_after_1_hour(self):
        order, _ = self._create_courier_order()
        # Push expiry past 1 hour ago
        ServiceOrder.objects.filter(pk=order.pk).update(
            courier_token_expires_at=timezone.now() - timedelta(seconds=10)
        )

        # Reading /api/orders/my/ immediately auto-cancels expired pending_location order
        my_orders = self.client.get('/api/orders/my/?page=1&lang=uz').json()
        card = my_orders['orders'][0]
        self.assertEqual(card['order_id'], order.order_id)
        self.assertEqual(card['status'], 'cancelled')
        self.assertEqual(card['bot_url'], '')

        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertIsNone(order.courier_token)

        # Also test direct background sweeper leaves fresh orders untouched while cancelling stale ones
        fresh_order, _ = self._create_courier_order()
        stale_order = ServiceOrder.objects.create(
            telegram_user=self.tg_user,
            client_name=self.tg_user.full_name,
            phone_number=self.tg_user.phone_number,
            phone=self.phone,
            comparison=self.comp,
            service_type='courier',
            status='pending_location',
            courier_token='stale_tok_123456',
            courier_token_expires_at=timezone.now() - timedelta(minutes=2),
        )
        expired_list = expire_stale_pending_courier_orders()
        self.assertEqual(len(expired_list), 1)
        self.assertEqual(expired_list[0]['order_id'], stale_order.order_id)

        stale_order.refresh_from_db()
        fresh_order.refresh_from_db()
        self.assertEqual(stale_order.status, 'cancelled')
        self.assertEqual(fresh_order.status, 'pending_location')


class ServerMaintenanceAndBackupRotationTests(TestCase):
    def test_backup_rotation_keeps_only_latest_2_and_cleans_temp_files(self):
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            bdir = Path(tmp)
            now_ts = time.time()
            # Create 5 fake .gz backups with distinct mtimes + 2 leftover temp files
            for idx in range(5):
                f = bdir / f"mobiprice_db_2026100{idx}_000000.sqlite3.gz"
                f.write_bytes(b"gzdata")
                os.utime(f, (now_ts - (10 - idx) * 60, now_ts - (10 - idx) * 60))

            (bdir / "leftover.sqlite3").write_bytes(b"raw")
            (bdir / "partial.sqlite3.gz.tmp").write_bytes(b"tmp")

            res = prune_old_backups(backup_dir=bdir, keep=2)
            self.assertEqual(res['deleted_gz'], 3)
            self.assertEqual(res['deleted_tmp'], 2)
            self.assertEqual(res['kept'], 2)

            remaining = sorted(p.name for p in bdir.iterdir())
            self.assertEqual(
                remaining,
                [
                    "mobiprice_db_20261003_000000.sqlite3.gz",
                    "mobiprice_db_20261004_000000.sqlite3.gz",
                ],
            )

    def test_cleanup_auth_tokens_sessions_excel_tmp_orphan_media_and_fsm_memory(self):
        import os
        import tempfile
        from pathlib import Path
        from django.contrib.sessions.models import Session

        now = timezone.now()

        # 1. Expired vs fresh AuthTokens
        old_tok = AuthToken.objects.create(
            token="old_expired_tok",
            session_key="s1",
            expires_at=now - timedelta(hours=3),
        )
        fresh_tok = AuthToken.objects.create(
            token="fresh_valid_tok",
            session_key="s2",
            expires_at=now + timedelta(minutes=5),
        )
        deleted_toks = cleanup_expired_auth_tokens(grace_hours=1)
        self.assertEqual(deleted_toks, 1)
        self.assertFalse(AuthToken.objects.filter(pk=old_tok.pk).exists())
        self.assertTrue(AuthToken.objects.filter(pk=fresh_tok.pk).exists())

        # 2. Expired vs valid Django Sessions
        Session.objects.create(session_key="expired_sess_1", session_data="abc", expire_date=now - timedelta(hours=2))
        Session.objects.create(session_key="valid_sess_1", session_data="abc", expire_date=now + timedelta(days=1))
        deleted_sess = cleanup_expired_sessions()
        self.assertEqual(deleted_sess, 1)
        self.assertTrue(Session.objects.filter(session_key="valid_sess_1").exists())

        # 3. Temp Excel files & orphan media & model photo replacement signal
        with tempfile.TemporaryDirectory() as media_tmp:
            media_root = Path(media_tmp)
            excel_dir = media_root / "excel_tmp"
            masters_dir = media_root / "masters"
            excel_dir.mkdir(parents=True)
            masters_dir.mkdir(parents=True)

            old_xlsx = excel_dir / "old_export.xlsx"
            old_xlsx.write_bytes(b"xlsx")
            old_ts = time.time() - 7200
            os.utime(old_xlsx, (old_ts, old_ts))

            fresh_xlsx = excel_dir / "fresh_export.xlsx"
            fresh_xlsx.write_bytes(b"xlsx")

            ref_photo = masters_dir / "master_active.jpg"
            ref_photo.write_bytes(b"img")
            old_orphan = masters_dir / "master_old_orphan.jpg"
            old_orphan.write_bytes(b"img")
            os.utime(old_orphan, (time.time() - 48 * 3600, time.time() - 48 * 3600))
            fresh_orphan = masters_dir / "master_fresh_upload.jpg"
            fresh_orphan.write_bytes(b"img")

            with override_settings(MEDIA_ROOT=media_root):
                master = TeamMember.objects.create(
                    full_name="Test Master",
                    role="Expert",
                    photo="masters/master_active.jpg",
                )
                self.assertEqual(cleanup_excel_tmp(max_age_minutes=60), 1)
                self.assertFalse(old_xlsx.exists())
                self.assertTrue(fresh_xlsx.exists())

                self.assertEqual(cleanup_orphan_media(min_age_hours=24), 1)
                self.assertFalse(old_orphan.exists())
                self.assertTrue(ref_photo.exists())
                self.assertTrue(fresh_orphan.exists())

                # Updating photo auto-deletes old file via pre_save signal
                new_photo = masters_dir / "master_new.jpg"
                new_photo.write_bytes(b"img2")
                master.photo = "masters/master_new.jpg"
                master.save()
                self.assertFalse(ref_photo.exists())
                self.assertTrue(new_photo.exists())

                # Deleting master auto-deletes current photo via post_delete signal
                master.delete()
                self.assertFalse(new_photo.exists())

        # 4. Aiogram MemoryStorage pruning removes empty entries and keeps active states
        storage = MemoryStorage()
        k_empty = StorageKey(bot_id=1, chat_id=10, user_id=10)
        k_active = StorageKey(bot_id=1, chat_id=20, user_id=20)
        asyncio.run(storage.set_state(k_empty, None))
        asyncio.run(storage.set_data(k_empty, {}))
        asyncio.run(storage.set_state(k_active, CourierLocationStates.waiting_for_location.state))
        asyncio.run(storage.set_data(k_active, {'courier_order_pk': 1}))

        pruned = prune_empty_fsm_memory(storage)
        self.assertEqual(pruned, 1)
        self.assertNotIn(k_empty, storage.storage)
        self.assertIn(k_active, storage.storage)
