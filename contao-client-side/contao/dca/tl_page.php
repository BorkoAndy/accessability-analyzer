<?php

/**
 * Contao Open Source CMS
 *
 * Copyright (c) 2005-2024 Leo Feyer
 *
 * @package   contao-client-side
 * @author    Antigravity AI
 * @license   LGPL
 */

use Contao\System;
use Symfony\Component\HttpFoundation\Request;

/**
 * Inject the A11y Analyzer script into the backend page settings
 */
try {
    $container = System::getContainer();
    $request = $container->get('request_stack')->getCurrentRequest() ?? Request::createFromGlobals();
    $scopeMatcher = $container->get('contao.routing.scope_matcher');

    if ($scopeMatcher->isBackendRequest($request)) {
        $GLOBALS['TL_JAVASCRIPT'][] = 'js/contao-a11y-analyzer.js';
    }
} catch (\Exception $e) {
    // Fallback for older Contao versions or early loading
    $GLOBALS['TL_JAVASCRIPT'][] = 'js/contao-a11y-analyzer.js';
}
