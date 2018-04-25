<?php
/**
 * PHP port of ECG TransportBridge.
 *
 * Author: Vivek Raghuram <vivek.raghuram@berkeley.edu>
 *
 */

class TransportBridge {

  private $buffer;

  function __construct() {
    global $wgTransportName;
    global $wgTransportAddr;
    global $wgTransportPort;

    $this->buffer = stream_socket_client(sprintf("tcp://%s:%d", $wgTransportAddr, $wgTransportPort),
                                   $errno,
                                   $errorMessage);

    if ($this->buffer === false) {
      throw new UnexpectedValueException("Failed to connect: $errorMessage");
    }

    $this->JOIN();
  }

  function __destruct() {
    fclose($this->buffer);
  }

  private function JOIN() {
    global $wgTransportName;
    $msg = array("JOIN", $wgTransportName);
    $msg_str = json_encode($msg);
    return $this->_send($msg_str);
  }

  private function SHOUT( $obj ) {
    global $wgTransportName;
    $msg = array("SHOUT", $wgTransportName, "FED1_ProblemSolver", $obj);
    $msg_str = json_encode($msg);
    return $this->_send($msg_str);
  }

  private function _send( $str ) {
    $len = strlen($str);
    $result = fwrite($this->buffer, sprintf("%d\n", $len));
    if ($result === false) {
      throw new UnexpectedValueException("Failed to send message");
    }

    $result = fwrite($this->buffer, $str);
    if ($result === false) {
      throw new UnexpectedValueException("Failed to send message");
    }
  }

  public function send( $obj ) {
    return $this->SHOUT($obj);
  }

  public function receive() {
    $start_time = time();
    $timeout = 30; // 30 second timeout

    while (time() - $start_time < $timeout) {
      $len_str = fgets($this->buffer, 16384);
      if (strlen($len_str) >= 10) {
        throw new UnexpectedValueException("Response length is insane: $len_str");
      }

      $len = (int) trim($len_str);
      if ($len <= 0) {
        throw new UnexpectedValueException("Response length is insanely short: $len_str");
      }

      $str = "";
      while($len - strlen($str) > 0) {
        $str .= fread($this->buffer, $len);
      }
      $obj = json_decode($str);
      // trigger_error($str);
      if ($obj[0] == "SHOUT" && $obj[2] == "Wiki") {
        return $obj[3];
      }
    }
    return false;
  }

}

?>
