model BSMWiperTest
  BSMWiperController controller;

equation
  // Ignition turns OFF at 9 seconds
  controller.IgnitionStatus = time < 9;

  // Wiper mode sequence
  controller.WiperSwitch =
    if time < 2 then 0
    else if time < 4 then 2
    else if time < 6 then 3
    else 1;

  // Rain sensor sequence
  controller.RainSensorLevel =
    if time < 6 then 0.0
    else if time < 8 then 0.5
    else 0.1;

  // Washer request between 7 and 7.5 seconds
  controller.WasherSwitch =
    time >= 7 and time < 7.5;

  controller.WiperParkSwitch = false;

end BSMWiperTest;
