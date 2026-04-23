<?php

/**
 * A11y Analyzer API Proxy v1.1
 * Bypasses CORS restrictions by handling requests server-side.
 *
 * DEBUG: set ?debug=1 in the URL to get extra info without sending to API.
 */

// ── CONFIGURATION ─────────────────────────────────────────────────────────────
define('DEFAULT_API_KEY', 'Kx9#mP2vN$qL8@wR5yT!');
// ──────────────────────────────────────────────────────────────────────────────

// Always return JSON — even for fatal errors
header('Content-Type: application/json; charset=utf-8');

// Catch real PHP errors and return them as JSON instead of HTML
// Ignore E_DEPRECATED (8192) and E_NOTICE (8) — these are non-fatal
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    if ($errno === E_DEPRECATED || $errno === E_USER_DEPRECATED
        || $errno === E_NOTICE   || $errno === E_USER_NOTICE) {
        return false; // let PHP handle it normally (log only)
    }
    http_response_code(500);
    echo json_encode([
        'error'   => 'PHP Error: ' . $errstr,
        'code'    => $errno,
        'file'    => basename($errfile),
        'line'    => $errline,
    ]);
    exit;
});

// Target API URL
$api_url = 'https://andy-a11y-analyzer.vercel.app/api/v1/full-audit';

// ── 1. Read POST body ────────────────────────────────────────────────────────
$input_data = file_get_contents('php://input');

if (empty($input_data)) {
    http_response_code(400);
    echo json_encode(['error' => 'No data provided to proxy', 'hint' => 'POST body was empty']);
    exit;
}

// ── 2. Get API key from headers (with PHP-FPM fallback) ──────────────────────
$api_key = '';

// Method A: getallheaders() (Apache / LiteSpeed)
if (function_exists('getallheaders')) {
    $all_headers = getallheaders();
    if (is_array($all_headers)) {
        // headers are case-insensitive — check both casings
        $api_key = $all_headers['X-API-Key']
                ?? $all_headers['x-api-key']
                ?? $all_headers['X-Api-Key']
                ?? '';
    }
}

// Method B: $_SERVER fallback (works on PHP-FPM / nginx)
if (empty($api_key)) {
    $api_key = $_SERVER['HTTP_X_API_KEY'] ?? '';
}

// Method C: Hardcoded fallback
if (empty($api_key)) {
    $api_key = DEFAULT_API_KEY;
}

// ── 3. Debug mode ─────────────────────────────────────────────────────────────
if (isset($_GET['debug'])) {
    $decoded = json_decode($input_data, true);
    echo json_encode([
        'debug'          => true,
        'api_url'        => $api_url,
        'api_key_found'  => !empty($api_key),
        'api_key_prefix' => !empty($api_key) ? substr($api_key, 0, 4) . '***' : '(none)',
        'body_bytes'     => strlen($input_data),
        'payload'        => $decoded,
        'getallheaders_available' => function_exists('getallheaders'),
    ]);
    exit;
}

// ── 4. Check curl is available ────────────────────────────────────────────────
if (!function_exists('curl_init')) {
    http_response_code(500);
    echo json_encode(['error' => 'PHP curl extension is not enabled on this server']);
    exit;
}

// ── 5. Forward to Vercel API via cURL ────────────────────────────────────────
$ch = curl_init($api_url);

curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $input_data,
    CURLOPT_HTTPHEADER     => [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($input_data),
        'X-API-Key: ' . $api_key,
        'User-Agent: Contao-A11y-Analyzer-Proxy/1.0',
    ],
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT        => 60,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_FOLLOWLOCATION => true,
]);

$response    = curl_exec($ch);
$curl_error  = curl_error($ch);
$curl_errno  = curl_errno($ch);
$http_status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
// curl_close() is a no-op since PHP 8.0 and deprecated in PHP 8.5 — omitted

// ── 6. Return result ──────────────────────────────────────────────────────────
if ($curl_error) {
    http_response_code(502);
    echo json_encode([
        'error'      => 'cURL Error: ' . $curl_error,
        'curl_errno' => $curl_errno,
    ]);
    exit;
}

http_response_code($http_status);
echo $response;
