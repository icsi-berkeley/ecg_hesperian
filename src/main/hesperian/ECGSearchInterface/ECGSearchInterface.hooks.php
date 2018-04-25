<?php
use MediaWiki\Widget\SearchInputWidget;
include('TransportBridge.php');

class ECGSearchInterfaceHooks {

  public static function searchPrepend( $specialSearch, $out, $term ) {
    $out->addModules("ECGSearchInterfaceModule");
    // return true;

    $out->enableOOUI();

		$searchWidget = new SearchInputWidget( [
			'id' => 'searchText',
			'name' => 'search',
			'autofocus' => trim( $term ) === '',
			'value' => $term,
			'dataLocation' => 'content',
			'infusable' => true,
		] );

		$layout = new \OOUI\ActionFieldLayout( $searchWidget, new \OOUI\ButtonInputWidget( [
			'type' => 'submit',
			'label' => $specialSearch->msg( 'searchbutton' )->text(),
			'flags' => [ 'progressive', 'primary' ],
		] ), [
			'align' => 'top',
		] );

		$out->addHTML(
      Xml::openElement(
  				'form',
  				[
  					'id' => 'search',
  					'method' => 'get',
  					'action' => wfScript(),
  				]
  			) .
  				'<div id="mw-search-top-table">' .
  					$layout .
  				'</div>' .
  				"<div class='mw-search-visualclear'></div>" .
  			'</form>'
      );

		$out->addHTML( "<div id='resultboxecg'>
                      <div id='resultboxgoogle-ecg' style='text-align:center'>
                        <div class='loading-icon'>
                          <div></div>
                          <div></div>
                          <div></div>
                        </div>
                      </div>
                    </div>
                    <div class='searchresults'>
                      <div id='resultboxgoogle-std' style='text-align:center'>
                        <div class='loading-icon'>
                          <div></div>
                          <div></div>
                          <div></div>
                        </div>
                      </div>
                    </div>" );


		# Do not return wiki results if configured that way
		return false;
  }
}
