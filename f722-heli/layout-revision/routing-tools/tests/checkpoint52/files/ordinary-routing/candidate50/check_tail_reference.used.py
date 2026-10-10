import sys,pathlib
H=pathlib.Path(__file__).resolve().parent; R=H.parents[2]
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
import check_critical_reference as c
c.I2C={};c.CRITICAL=['TAIL_MCU','TAIL_EXT','SERVO3_MCU','RPM_LV','ADC_DIV_MID','+3V3_CORE']
c.main()
