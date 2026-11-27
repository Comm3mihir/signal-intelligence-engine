-- Enable Supabase Cron and pg_net. Create these Vault entries separately:
-- signal_backend_url (HTTPS deployment base URL) and signal_scheduler_secret.
-- Run with a trusted operator role in the Supabase SQL Editor.
select cron.schedule(
  'signal-intelmap-worker',
  '* * * * *',
  $job$
  select net.http_post(
    url := rtrim(url.decrypted_secret, '/') || '/api/intelmap/workflows/tick',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || token.decrypted_secret,
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 55000
  )
  from vault.decrypted_secrets url
  cross join vault.decrypted_secrets token
  where url.name = 'signal_backend_url' and token.name = 'signal_scheduler_secret';
  $job$
);
