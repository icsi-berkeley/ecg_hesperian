<?php
/**
 * ECGSearchInterface Extension - communicates with ECG system
 *
 * Author: Vivek Raghuram <vivek.raghuram@berkeley.edu>
 *
 */

if ( function_exists( 'wfLoadExtension' ) ) {
  wfLoadExtension( 'ECGSearchInterface' );
  // Keep i18n globals so mergeMessageFileList.php doesn't break
  $wgMessagesDirs['ECGSearchInterface'] = __DIR__ . '/i18n';
  wfWarn(
    'Deprecated PHP entry point used for ECGSearchInterface extension. ' .
    'Please use wfLoadExtension instead, ' .
    'see https://www.mediawiki.org/wiki/Extension_registration for more details.'
  );
  return;
}

$extensionJsonFilename = dirname( __FILE__ ) . '/extension.json';
$extensionJsonData = FormatJson::decode( file_get_contents( $extensionJsonFilename ), true );
$wgExtensionCredits[$extensionJsonData['type']][] = array(
  'path' => __FILE__,
  'name' => $extensionJsonData['name'],
  'author' => $extensionJsonData['author'],
  'descriptionmsg' => $extensionJsonData['descriptionmsg'],
  'version' => $extensionJsonData['version'],
);

# Define extension hooks
$wgAutoloadClasses['ECGSearchInterface'] = __DIR__ . '/ECGSearchInterface.hooks.php';

# Hook into SpecialSearchResultsPrepend
$wgHooks['SpecialSearchResultsPrepend'][] = 'ECGSearchInterfaceHooks::searchPrepend';
