<?php
// Plain PHP tests for the tag builder. Run: php tests/ActionTest.php

require __DIR__ . '/../plugins/actions/privatusanalytics/privatusanalytics.php';

$failures = 0;
function check($name, $expected, $actual)
{
	global $failures;
	if ($expected === $actual) {
		echo "ok   $name\n";
		return;
	}
	$failures++;
	echo "FAIL $name\n  expected: " . var_export($expected, true) . "\n  actual:   " . var_export($actual, true) . "\n";
}

$src = '<script defer src="https://privatusstats.com/js/pa.js"';
check('full tag', $src . ' data-site="pa_abc123" data-modules="engage,auto,vitals,clicks,ask"></script>', privatus_analytics_tag('pa_abc123', 'engage,auto,vitals,clicks,ask'));
check('modules in standard order, unknown dropped', $src . ' data-site="pa_abc" data-modules="engage,vitals"></script>', privatus_analytics_tag('pa_abc', 'vitals, evil", engage'));
check('no modules gives empty attribute', $src . ' data-site="pa_abc" data-modules=""></script>', privatus_analytics_tag('pa_abc', ''));
check('empty site id', '', privatus_analytics_tag('', 'engage'));
check('bare prefix', '', privatus_analytics_tag('pa_', 'engage'));
check('quote in site id', '', privatus_analytics_tag('pa_x" onload="alert(1)', 'engage'));
check('trailing newline', '', privatus_analytics_tag("pa_abc\n", 'engage'));
check('escaped html entity form', '', privatus_analytics_tag('pa_x&quot;', 'engage'));

echo $failures === 0 ? "\nAll tests passed.\n" : "\n$failures failed.\n";
exit($failures === 0 ? 0 : 1);
