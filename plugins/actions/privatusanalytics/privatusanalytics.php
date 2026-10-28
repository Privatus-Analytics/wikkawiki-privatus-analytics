<?php
/**
 * Privatus Analytics action for WikkaWiki.
 *
 * Prints the Privatus Analytics tracking script. Cookieless website analytics,
 * with bots left out. See https://privatusanalytics.com
 *
 * Site-wide use (recommended): add this line to your theme's header.php, just
 * before </head>:
 *
 *     <?php echo $this->Action('privatusanalytics'); ?>
 *
 * Settings go in wikka.config.php:
 *
 *     'privatus_site_id' => 'pa_YOURSITEID',
 *     'privatus_modules' => 'engage,auto,vitals,clicks,ask',   // optional
 *     'privatus_skip_admins' => '1',                           // optional
 *
 * You can also pass them to the action: {{privatusanalytics site="pa_YOURSITEID" modules="engage,vitals"}}
 *
 * @package    Actions
 * @name       privatusanalytics
 * @version    1.0.0
 * @license    MIT (c) 2026 Two Phase LLC
 * @link       https://github.com/Privatus-Analytics/wikkawiki-privatus-analytics
 *
 * @input      string $site     optional: site ID, overrides privatus_site_id
 * @input      string $modules  optional: comma-separated modules, overrides privatus_modules
 * @output     the script tag, or nothing when the site ID is missing or not valid
 */

if (!defined('PRIVATUS_ANALYTICS_MODULES')) {
	define('PRIVATUS_ANALYTICS_MODULES', 'engage,auto,vitals,clicks,ask');
}

if (!function_exists('privatus_analytics_tag')) {
	/**
	 * Builds the script tag. Returns '' when the site ID is not valid.
	 *
	 * @param string $site_id
	 * @param string $modules comma-separated list, unknown names are dropped
	 * @return string
	 */
	function privatus_analytics_tag($site_id, $modules)
	{
		if (!is_string($site_id) || !preg_match('/^pa_[A-Za-z0-9]+$/D', $site_id)) {
			return '';
		}
		$wanted = array_map('trim', explode(',', (string) $modules));
		$known = explode(',', PRIVATUS_ANALYTICS_MODULES);
		$list = array();
		foreach ($known as $module) {
			if (in_array($module, $wanted, true)) {
				$list[] = $module;
			}
		}
		return '<script defer src="https://privatusstats.com/js/pa.js"'
			. ' data-site="' . htmlspecialchars($site_id, ENT_QUOTES, 'UTF-8') . '"'
			. ' data-modules="' . htmlspecialchars(implode(',', $list), ENT_QUOTES, 'UTF-8') . '"></script>';
	}
}

if (isset($this) && is_object($this)) {
	$privatus_site_id = isset($vars['site']) ? $vars['site'] : $this->GetConfigValue('privatus_site_id', '');
	$privatus_modules = isset($vars['modules']) ? $vars['modules'] : $this->GetConfigValue('privatus_modules', PRIVATUS_ANALYTICS_MODULES);
	$privatus_skip_admins = (string) $this->GetConfigValue('privatus_skip_admins', '1') === '1';

	if (!($privatus_skip_admins && $this->IsAdmin()) && empty($GLOBALS['privatus_analytics_printed'])) {
		$privatus_tag = privatus_analytics_tag((string) $privatus_site_id, (string) $privatus_modules);
		if ($privatus_tag !== '') {
			$GLOBALS['privatus_analytics_printed'] = true;
			echo $privatus_tag . "\n";
		}
	}
}
?>
