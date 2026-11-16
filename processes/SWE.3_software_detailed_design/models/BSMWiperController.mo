model InputValidator
  input Integer RawWiperSwitchSignal;
  input Integer RawRainIntensitySignal;
  input Boolean RawWasherRequestSignal;
  input Integer RawIgnitionStatusSignal;

  output Integer ValidatedWiperSwitchSignal;
  output Integer ValidatedRainIntensity;
  output Boolean ValidatedWasherRequest;
  output Integer IgnitionStatus;
  output Boolean InputFaultDetected;

algorithm
  // ASSUMPTION ASM-001: Raw input signals must fall within defined valid bounds (Switch: 0-4, Rain: 0-100, Ignition: 0-1).
  if RawWiperSwitchSignal < 0 or RawWiperSwitchSignal > 4 or
     RawRainIntensitySignal < 0 or RawRainIntensitySignal > 100 or
     RawIgnitionStatusSignal < 0 or RawIgnitionStatusSignal > 1 then
    InputFaultDetected := true;
    ValidatedWiperSwitchSignal := 0;
    ValidatedRainIntensity := 0;
    ValidatedWasherRequest := false;
    IgnitionStatus := 0;
  else
    InputFaultDetected := false;
    ValidatedWiperSwitchSignal := RawWiperSwitchSignal;
    ValidatedRainIntensity := RawRainIntensitySignal;
    ValidatedWasherRequest := RawWasherRequestSignal;
    IgnitionStatus := RawIgnitionStatusSignal;
  end if;
end InputValidator;

model SwitchDecoder
  input Integer ValidatedWiperSwitchSignal;
  input Boolean InputFaultDetected;

  output Integer DecodedWiperMode;

algorithm
  if InputFaultDetected then
    DecodedWiperMode := 0;
  else
    DecodedWiperMode := ValidatedWiperSwitchSignal;
  end if;
end SwitchDecoder;

model IntermittentAndAutoWipeController
  input Integer DecodedWiperMode;
  input Integer ValidatedRainIntensity;
  input Real IntermittentIntervalConfig;

  output Integer DesiredWiperSpeed;

protected
  Real cycleTime;
  Real tInCycle;

algorithm
  if DecodedWiperMode == 2 then
    DesiredWiperSpeed := 1;
  elseif DecodedWiperMode == 3 then
    DesiredWiperSpeed := 2;
  elseif DecodedWiperMode == 4 then
    // ASSUMPTION ASM-003: Rain intensity thresholds are 0 for OFF, 1..50 for LOW, and >50 for HIGH.
    if ValidatedRainIntensity == 0 then
      DesiredWiperSpeed := 0;
    elseif ValidatedRainIntensity <= 50 then
      DesiredWiperSpeed := 1;
    else
      DesiredWiperSpeed := 2;
    end if;
  elseif DecodedWiperMode == 1 then
    // ASSUMPTION ASM-002: Intermittent active pulse duration is fixed at 1.0 second per cycle.
    cycleTime := 1.0 + (if IntermittentIntervalConfig < 0.1 then 0.1 else IntermittentIntervalConfig);
    tInCycle := time - floor(time / cycleTime) * cycleTime;
    if tInCycle <= 1.0 then
      DesiredWiperSpeed := 1;
    else
      DesiredWiperSpeed := 0;
    end if;
  else
    DesiredWiperSpeed := 0;
  end if;
end IntermittentAndAutoWipeController;

model WasherAndIgnitionManager
  input Boolean ValidatedWasherRequest;
  input Integer IgnitionStatus;

  output Boolean WasherPumpCommand;
  output Boolean IgnitionLockoutActive;

algorithm
  if IgnitionStatus == 0 then
    IgnitionLockoutActive := true;
    WasherPumpCommand := false;
  else
    IgnitionLockoutActive := false;
    WasherPumpCommand := ValidatedWasherRequest;
  end if;
end WasherAndIgnitionManager;

model ParkPositionAndActuationController
  input Integer DesiredWiperSpeed;
  input Boolean ParkPositionState;

  output Integer TargetWiperSpeed;

algorithm
  if DesiredWiperSpeed == 1 or DesiredWiperSpeed == 2 then
    TargetWiperSpeed := DesiredWiperSpeed;
  elseif DesiredWiperSpeed == 0 and not ParkPositionState then
    // ASSUMPTION ASM-004: Unparked wiper completes cycle to rest position at LOW speed (1).
    TargetWiperSpeed := 1;
  else
    TargetWiperSpeed := 0;
  end if;
end ParkPositionAndActuationController;

model MotorOutputInterlock
  input Integer TargetWiperSpeed;
  input Boolean WasherPumpCommand;
  input Boolean IgnitionLockoutActive;

  output Boolean LowSpeedMotorDriverCmd;
  output Boolean HighSpeedMotorDriverCmd;
  output Boolean WasherPumpDriverCmd;

algorithm
  if IgnitionLockoutActive then
    LowSpeedMotorDriverCmd := false;
    HighSpeedMotorDriverCmd := false;
    WasherPumpDriverCmd := false;
  else
    if TargetWiperSpeed == 2 then
      HighSpeedMotorDriverCmd := true;
      LowSpeedMotorDriverCmd := false;
    elseif TargetWiperSpeed == 1 then
      LowSpeedMotorDriverCmd := true;
      HighSpeedMotorDriverCmd := false;
    else
      LowSpeedMotorDriverCmd := false;
      HighSpeedMotorDriverCmd := false;
    end if;
    WasherPumpDriverCmd := WasherPumpCommand;
  end if;
end MotorOutputInterlock;

model BSMWiperController
  input Integer RawWiperSwitchSignal;
  input Integer RawRainIntensitySignal;
  input Boolean RawWasherRequestSignal;
  input Integer RawIgnitionStatusSignal;
  input Real IntermittentIntervalConfig;
  input Boolean ParkPositionState;

  output Boolean LowSpeedMotorDriverCmd;
  output Boolean HighSpeedMotorDriverCmd;
  output Boolean WasherPumpDriverCmd;
  output Boolean InputFaultDetected;

  InputValidator inputValidator;
  SwitchDecoder switchDecoder;
  IntermittentAndAutoWipeController intermittentAndAutoWipeController;
  WasherAndIgnitionManager washerAndIgnitionManager;
  ParkPositionAndActuationController parkPositionAndActuationController;
  MotorOutputInterlock motorOutputInterlock;

equation
  inputValidator.RawWiperSwitchSignal = RawWiperSwitchSignal;
  inputValidator.RawRainIntensitySignal = RawRainIntensitySignal;
  inputValidator.RawWasherRequestSignal = RawWasherRequestSignal;
  inputValidator.RawIgnitionStatusSignal = RawIgnitionStatusSignal;

  switchDecoder.ValidatedWiperSwitchSignal = inputValidator.ValidatedWiperSwitchSignal;
  switchDecoder.InputFaultDetected = inputValidator.InputFaultDetected;

  intermittentAndAutoWipeController.DecodedWiperMode = switchDecoder.DecodedWiperMode;
  intermittentAndAutoWipeController.ValidatedRainIntensity = inputValidator.ValidatedRainIntensity;
  intermittentAndAutoWipeController.IntermittentIntervalConfig = IntermittentIntervalConfig;

  washerAndIgnitionManager.ValidatedWasherRequest = inputValidator.ValidatedWasherRequest;
  washerAndIgnitionManager.IgnitionStatus = inputValidator.IgnitionStatus;

  parkPositionAndActuationController.DesiredWiperSpeed = intermittentAndAutoWipeController.DesiredWiperSpeed;
  parkPositionAndActuationController.ParkPositionState = ParkPositionState;

  motorOutputInterlock.TargetWiperSpeed = parkPositionAndActuationController.TargetWiperSpeed;
  motorOutputInterlock.WasherPumpCommand = washerAndIgnitionManager.WasherPumpCommand;
  motorOutputInterlock.IgnitionLockoutActive = washerAndIgnitionManager.IgnitionLockoutActive;

  LowSpeedMotorDriverCmd = motorOutputInterlock.LowSpeedMotorDriverCmd;
  HighSpeedMotorDriverCmd = motorOutputInterlock.HighSpeedMotorDriverCmd;
  WasherPumpDriverCmd = motorOutputInterlock.WasherPumpDriverCmd;
  InputFaultDetected = inputValidator.InputFaultDetected;
end BSMWiperController;