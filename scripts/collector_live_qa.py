"""Bounded paused-collector QA using a temporary native DPAPI configuration.

No secrets in argv, files, environment exports or output. Uses curl's stdin
configuration so request credentials never enter its process arguments.
Only synthetic example.invalid records, always marked with the private QA key.
Non-secret file checkpoints allow native restricted SQL fixture verification.
"""
import base64
import json
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from protect_validation_config import load_config

EXPECTED = 'https://br-polished-feather-ba3h1u8g-evidence.compute.c-8.eu-central-1.aws.neon.tech'
ORIGIN = 'https://venture-ai-ceo-evaluator.onrender.com'
CONSENT = '2026-10-19-v2'


def main():
    print('QA_STARTED', flush=True)
    config = load_config()
    if config.get('endpoint') != EXPECTED or urlsplit(config['endpoint']).scheme != 'https':
        raise RuntimeError('Unexpected QA destination')
    checks = []
    tokens, receipts = [], []

    def check(name, condition):
        if not condition:
            raise RuntimeError(name)
        checks.append(name)

    def quote(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'

    def request(path, body=None, method=None, bearer=None, qa=False, origin=ORIGIN, extra=None, content_type='application/json'):
        method = method or ('POST' if body is not None else 'GET')
        headers = {'Origin': origin, 'User-Agent': 'VentureValidation-QA/1.0'}
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        if qa:
            headers['X-Validation-QA'] = config['qaKey']
        if body is not None:
            headers['Content-Type'] = content_type
        headers.update(extra or {})
        lines = ['silent', 'show-error', 'include', 'suppress-connect-headers', 'max-time = 25',
                 'max-filesize = 16384', 'url = ' + quote(EXPECTED + path), 'request = ' + quote(method),
                 'write-out = "\\n%{http_code}"']
        lines.extend('header = ' + quote(k + ': ' + v) for k, v in headers.items())
        if body is not None:
            lines.append('data = ' + quote(json.dumps(body, separators=(',', ':'))))
        p = subprocess.run(['curl.exe', '-q', '--config', '-'], input='\n'.join(lines),
                           text=True, capture_output=True, timeout=30)
        if p.returncode:
            raise RuntimeError('HTTPS transport failed (curl ' + str(p.returncode) + ')')
        payload, code = p.stdout.rsplit('\n', 1)
        head, raw = payload.split('\n\n', 1)
        response_headers = {k.lower(): v.strip() for line in head.splitlines()[1:] if ':' in line for k, v in [line.split(':', 1)]}
        try:
            value = json.loads(raw) if raw.strip() else {}
        except ValueError:
            raise RuntimeError('Expected application JSON') from None
        return int(code), value, response_headers

    def expect(name, path, expected, body=None, **kwargs):
        status, value, headers = request(path, body, **kwargs)
        check(name, status == expected)
        return value, headers

    session = {'consent': CONSENT, 'measurement': True, 'role': 'agency', 'source': 'other', 'website': '', 'automated': False}
    email = 'activation-' + uuid.uuid4().hex + '@example.invalid'
    interest = {'email': email, 'role': 'agency', 'platform': 'shopify', 'timing': '30days', 'problem': 'handoff',
                'pilot': True, 'willingness': 'yes', 'price_cents': 900, 'currency': 'EUR', 'consent': CONSENT, 'website': ''}
    baseline = None
    def checkpoint(stage, filename):
        Path('.tmp/collector-qa-stage.json').write_text(json.dumps({'stage': stage}), encoding='utf-8')
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            path = Path('.tmp', filename)
            if path.exists():
                value = json.loads(path.read_text(encoding='utf-8'))
                path.unlink()
                return value
            time.sleep(0.5)
        raise RuntimeError('Native QA checkpoint timed out')
    try:
        status, _ = expect('application_status', '/status', 200)
        check('collection_stopped', status.get('application') == 'venture-validation' and status.get('collection_enabled') is False)
        check('payments_uploads_disabled', status.get('payments_enabled') is False and status.get('uploads_enabled') is False)
        expect('summary_requires_auth', '/summary', 401)
        expect('diagnostics_requires_qa', '/diagnostics', 401)
        security, _ = expect('runtime_diagnostics', '/diagnostics', 200, qa=True)
        check('restricted_database_tls', security == {'role': 'venture_collector', 'privileged': False, 'can_create': False, 'can_verify': False, 'tls': True, 'tls_authorized': True})
        baseline, _ = expect('summary_read_access', '/summary', 200, bearer=config['readKey'])
        expect('public_shutdown', '/session', 503, session)
        _, headers = expect('cors_preflight', '/session', 204, method='OPTIONS', extra={'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type,authorization'})
        check('cors_exact_origin', headers.get('access-control-allow-origin') == ORIGIN and 'POST' in headers.get('access-control-allow-methods', ''))
        _, denied = expect('foreign_origin_denied', '/session', 403, session, qa=True, origin='https://untrusted.example.invalid')
        check('foreign_origin_no_cors', 'access-control-allow-origin' not in denied)
        expect('method_enforced', '/session', 405, qa=True)
        expect('consent_required', '/session', 400, {**session, 'consent': False}, qa=True)
        expect('extra_catalog_field_denied', '/session', 400, {**session, 'csv': 'synthetic'}, qa=True)
        expect('body_limit', '/session', 413, {'x': 'x' * 5000}, qa=True)
        expect('json_required', '/session', 415, session, qa=True, content_type='text/plain')
        expect('bot_excluded', '/session', 403, session, qa=True, extra={'User-Agent': 'Googlebot'})
        expect('no_upload', '/upload', 404, {}, qa=True)
        expect('no_checkout', '/checkout', 404, {}, qa=True)
        made, _ = expect('qa_session', '/session', 201, session, qa=True)
        token = made['token']; tokens.append(token)
        expect('engagement_age_enforced', '/event', 400, {'event': 'engaged'}, bearer=token, qa=True)
        expect('evaluation_requires_interaction', '/event', 400, {'event': 'evaluation_complete'}, bearer=token, qa=True)
        time.sleep(2.2)
        for change in [{'consent': False}, {'price_cents': 100}, {'currency': 'USD'}, {'independently_verified': True}]:
            expect('registration_validation_' + next(iter(change)), '/interest', 400, {**interest, **change}, bearer=token, qa=True)
        saved, _ = expect('synthetic_registration', '/interest', 201, interest, bearer=token, qa=True)
        receipt = saved['receipt']; receipts.append(receipt)
        check('no_order_or_verified_email', saved.get('paid_order') is False and saved.get('email_verified') is False)
        expect('duplicate_email_denied', '/interest', 400, interest, bearer=token, qa=True)
        no_metrics, _ = expect('registration_without_measurement', '/session', 201, {**session, 'measurement': False}, qa=True)
        tokens.append(no_metrics['token'])
        expect('separate_measurement_consent', '/event', 403, {'event': 'interaction'}, bearer=no_metrics['token'], qa=True)
        time.sleep(8.5)
        for event in ['engaged', 'interaction', 'evaluation_complete', 'report_download', 'sample']:
            expect('qa_' + event, '/event', 200, {'event': event}, bearer=token, qa=True)
        after, _ = expect('summary_excludes_all_qa', '/summary', 200, bearer=config['readKey'])
        check('genuine_metrics_unchanged', after == baseline)
        print('QA_WAITING_FOR_ENCRYPTION_FIXTURE', flush=True)
        fixture = checkpoint('encryption_fixture', 'collector-qa-encryption.json')
        js = "import{createDecipheriv}from'node:crypto';let s='';for await(const c of process.stdin)s+=c;const v=JSON.parse(s),b=Buffer.from(v.cipher,'base64'),k=Buffer.from(v.key,'base64');function dec(key){const d=createDecipheriv('aes-256-gcm',key,b.subarray(0,12));d.setAuthTag(b.subarray(12,28));return Buffer.concat([d.update(b.subarray(28)),d.final()]).toString();}const ok=dec(k)===v.expected;k[0]^=1;let rejected=false;try{dec(k);}catch{rejected=true;}process.stdout.write(JSON.stringify({ok,rejected}));"
        p = subprocess.run(['node', '--input-type=module', '-e', js], input=json.dumps({'cipher': fixture['encrypted_contact'], 'key': config['contactKey'], 'expected': email}), text=True, capture_output=True, timeout=10)
        check('authenticated_contact_encryption', p.returncode == 0 and json.loads(p.stdout) == {'ok': True, 'rejected': True})
        expect('receipt_withdrawal_while_paused', '/withdraw', 200, {'receipt': receipt})
        receipts.clear()
        for t in tokens:
            expect('session_deletion_while_paused', '/forget', 200, {}, bearer=t)
        tokens.clear()
        print('QA_WAITING_FOR_RETENTION_AND_QUOTA_FIXTURES', flush=True)
        if checkpoint('retention_fixture', 'collector-qa-retention.json').get('fixtures_ready') is not True:
            raise RuntimeError('QA fixtures not authorized')
        _, headers = expect('database_daily_cap', '/session', 429, session, qa=True)
        check('retry_after_on_quota', headers.get('retry-after') == '3600')
        final, _ = expect('purge_and_aggregate_access', '/summary', 200, bearer=config['readKey'])
        check('qa_did_not_change_customer_metrics', final == baseline)
        print('QA_WAITING_FOR_DATABASE_CLEANUP_CONFIRMATION', flush=True)
        if checkpoint('cleanup_confirmation', 'collector-qa-cleanup.json').get('database_checks_passed') is not True:
            raise RuntimeError('Database cleanup unverified')
        result = {'passed': True, 'checks': checks, 'genuine_summary_before': baseline, 'genuine_summary_after': final,
                  'synthetic_records_excluded': True, 'collection_stopped_during_qa': True, 'no_contact_values_in_output': True}
        Path('.tmp/collector-live-qa-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'live_qa_passed': True, 'checks_passed': len(checks)}), flush=True)
    except Exception as error:
        # RuntimeError labels are fixed strings. Never print a transport response or input.
        print(json.dumps({'live_qa_passed': False, 'checks_passed': len(checks), 'failed_check': str(error) if type(error) is RuntimeError else type(error).__name__}), flush=True)
        raise SystemExit(1) from None
    finally:
        for receipt in receipts:
            try: request('/withdraw', {'receipt': receipt})
            except Exception: pass
        for token in tokens:
            try: request('/forget', {}, bearer=token)
            except Exception: pass


if __name__ == '__main__':
    main()
