model BSMWiperTest
  BSMWiperController controller;

equation
  // Driving inputs deterministically as functions of simulation time
  controller.RawIgnitionStatusSignal = if time < 1.0 then 0 else 1;
  controller.RawWiperSwitchSignal = if time < 1.0 then 2
                                    else if time < 3.0 then 2
                                    else if time < 4.0 then 3
                                    else if time < 6.0 then 0
                                    else if time < 7.0 then 0
                                    else if time < 8.0 then 4
                                    else if time < 9.0 then 99
                                    else 0;
  controller.RawRainIntensitySignal = if time >= 7.0 and time < 8.0 then 80 else 0;
  controller.RawWasherRequestSignal = if time >= 6.0 and time < 7.0 then true else false;
  controller.IntermittentIntervalConfig = 2.0;
  controller.ParkPositionState = if time >= 4.0 and time < 5.0 then false else true;

  // Assertions for verification against software and system requirements

  // TC-001 [SWE-010, SYS-008]: Ignition lockout enforcement
  assert(not (time >= 0.1 and time < 0.9) or (not controller.LowSpeedMotorDriverCmd and not controller.HighSpeedMotorDriverCmd and not controller.WasherPumpDriverCmd),
         "TC-001 Failed: Ignition lockout must deactivate all outputs when ignition status is 0.");

  // TC-002 [SWE-001, SWE-002, SYS-001, SYS-002]: Low speed wiper operation
  assert(not (time >= 1.1 and time < 2.9) or (controller.LowSpeedMotorDriverCmd and not controller.HighSpeedMotorDriverCmd),
         "TC-002 Failed: Low speed wiper command should be active when LOW mode is selected and ignition is active.");

  // TC-003 [SWE-003, SWE-008, SYS-002, SYS-006]: High speed wiper operation & mutual exclusion
  assert(not (time >= 3.1 and time < 3.9) or (controller.HighSpeedMotorDriverCmd and not controller.LowSpeedMotorDriverCmd),
         "TC-003 Failed: High speed wiper command active and mutual exclusion must prevent low speed motor command.");

  // TC-004 [SWE-007, SYS-005]: Park position return cycle (depends on ASM-004)
  assert(not (time >= 4.1 and time < 4.9) or (controller.LowSpeedMotorDriverCmd and not controller.HighSpeedMotorDriverCmd),
         "TC-004 Failed: Wiper must maintain low-speed motor actuation until park switch returns true.");

  // TC-005 [SWE-006, SYS-004]: Washer pump actuation
  assert(not (time >= 6.1 and time < 6.9) or controller.WasherPumpDriverCmd,
         "TC-005 Failed: Washer pump driver command must activate when washer request is true and ignition is active.");

  // TC-006 [SWE-005, SYS-003]: Automatic rain sensing control (depends on ASM-003)
  assert(not (time >= 7.1 and time < 7.9) or controller.HighSpeedMotorDriverCmd,
         "TC-006 Failed: Rain intensity 80 under AUTO mode must trigger high speed wiping.");

  // TC-007 [SWE-009, SYS-007]: Input signal range validation & safe state (depends on ASM-001)
  assert(not (time >= 8.1 and time < 8.9) or (controller.InputFaultDetected and not controller.LowSpeedMotorDriverCmd and not controller.HighSpeedMotorDriverCmd),
         "TC-007 Failed: Out-of-range switch input signal 99 must trigger fault state and force motor outputs to inactive.");
end BSMWiperTest;