import sys,pathlib
H=pathlib.Path(__file__).resolve().parent; R=H.parents[2]
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
import export_signal_snapshot as e
e.I2C={};e.CRITICAL=['SERVO1_MCU','SERVO2_MCU','ESC_MCU','RPM_LV','ADC_BUS','ADC_DIV_MID','TAIL_MCU','EFUSE_EN','VX_RAW']
e.main()
