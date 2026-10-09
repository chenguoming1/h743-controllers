#include <stdio.h>
#include <stdint.h>
#include "src/main/drivers/bus_i2c_timing.h"
int main(void) {
    const uint32_t pclk[] = {54000000, 60000000};
    for (unsigned i=0; i<sizeof(pclk)/sizeof(pclk[0]); ++i) {
        uint32_t r=i2cClockTIMINGR(pclk[i],800,0);
        printf("PCLK1=%u requested_kHz=800 DNF=0 TIMINGR=0x%08X PRESC=%u SCLDEL=%u SDADEL=%u SCLH=%u SCLL=%u\n",pclk[i],r,(r>>28)&15,(r>>20)&15,(r>>16)&15,(r>>8)&255,r&255);
    }
    return 0;
}
