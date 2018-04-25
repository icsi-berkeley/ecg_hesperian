<?php
include('TransportBridge.php');

class ECGSearchInterfaceAPI extends ApiBase {

  public function execute() {
    $params = $this->extractRequestParams();
    $bridge = new TransportBridge();
    if ($params['clarification'] > 0) {
      $params['clarification'] = array(
        'field' => $params['clarification_field'],
        'type' => $params['clarification_type'],
        'text' => $params['clarification_text'],
        'val'  => $params['clarification_val']
      );
    } else {
      $params['clarification'] = false;
    }
    $bridge->send($params);

    $response = $bridge->receive();
    if ($response == false) {
      $this->getResult()->addValue( null, $this->getModuleName(), array('fail' => 'true') );
    } else {
      $this->getResult()->addValue( null, $this->getModuleName(), $response );
    }
  }

  public function getAllowedParams() {
		return array(
      'sid' => array(
        ApiBase::PARAM_TYPE => 'password'
			),
			'query' => array(
				ApiBase::PARAM_REQUIRED => true,
        ApiBase::PARAM_TYPE => 'string'
			),
      'clarification' => array(
        ApiBase::PARAM_REQUIRED => true,
        ApiBase::PARAM_TYPE => 'integer' // for some reason this was always true if boolean
      ),
      'clarification_field' => array(
        ApiBase::PARAM_TYPE => 'string'
      ),
      'clarification_type' => array(
        ApiBase::PARAM_TYPE => 'string'
      ),
      'clarification_text' => array(
        ApiBase::PARAM_TYPE => 'string'
      ),
      'clarification_val' => array(
        ApiBase::PARAM_TYPE => 'string'
      )
		);
	}

}
