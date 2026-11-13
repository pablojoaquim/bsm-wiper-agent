model BSMWiperController
  // Inputs
  input Integer WiperSwitch
    "0=OFF, 1=INTERMITTENT, 2=LOW, 3=HIGH";

  input Real RainSensorLevel
    "Rain intensity: 0.0 to 1.0";

  input Boolean WasherSwitch
    "Driver washer request";

  input Boolean IgnitionStatus
    "Ignition ON/OFF";

  input Boolean WiperParkSwitch
    "Wiper at rest position";

  // Outputs
  output Boolean WiperMotorLow;
  output Boolean WiperMotorHigh;
  output Boolean WasherPump;

equation
  // Low speed operation
  WiperMotorLow =
    IgnitionStatus and (
      WiperSwitch == 2 or
      (WiperSwitch == 1 and RainSensorLevel > 0.3)
    );

  // High speed operation
  WiperMotorHigh =
    IgnitionStatus and (WiperSwitch == 3);

  // Washer pump operation
  WasherPump =
    IgnitionStatus and WasherSwitch;

end BSMWiperController;
