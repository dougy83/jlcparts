# some lists of attribute names not included in the standard lists
# entries that are commented out need special parsers to be usable

freqattr = [
    "-3db bandwidth",
    "-3db bandwidth(g=1)",
    "bandwidth",
    "bandwidth (-3db)",
    "center frequency",
#    "central frequency",
    "clock frequency",
#    "clock frequency (fc)",
    "clock frequency (max)",
#    "frequency",
#    "frequency - cutoff or center",
#    "frequency bands (low / high)",
#    "frequency range",
    "frequency-max",
#    "inductance @ frequency",
    "nominal frequency",
    "resonant frequency",
#    "switch frequency",
#    "switching frequency",
#    "transition frequency (ft)",
    "Gain bandwidth product(gbp)",
    "working frequency"
    ]

resattr = [
    "coil resistance",
    "contact resistance",
    "dark resistance",
    "insulation resistance (min)",
    "insulation resistance",
    "nominal cold resistance",
    "on resistance",
    "on-state resistance (max)",
    "resistance - initial (ri) (min)",
    "resistance - post trip (r1) (max)",
    "resistance value",
    "static drain-source on resistance (rds(on))"
    ]

powerattr = [
    "average gate power dissipation (pg(av))",
    "coil rated power",
#    "power dissipation",
    "current rating - power (max)",
    "dissipation power",
    "dissipation power(max)",
    "max power",
    "maximum power",
    "maximum switching power",
    "power rating",
    "rated power"
    ]

currentattr = [
    "average rectified current (io)",
    "nominal impulse discharge current",
    "bias current",
    "breakover current (ibo)",
#    "clamp diode leakage current (ir@vr)",
    "collector current (ic)",
    "collector current (ic)",
    "collector current (max)",
    "collector current(ic)",
    "collector cut-off current (icbo)",
#    "collector cut-off current (icbo@vcb)",
#    "collector cut-off current (ices@vce)",
    "collector dark current",
    "contact current",
    "contact current (ac)",
    "contact current (dc)",
    "continuous drain current (id)",
    "continuous drain current (id)",
    "continuous load current",
    "current - dc forward (if)",
    "current - input bias(ib)",
    "current - saturation (isat)",
    "current consumption",
    "current dark",
    "current of transmitting",
    "current range",
    "current rating (ac)",
    "current rating (dc)",
    "current rating - power (max)",
    "dark current",
    "digit drive current",
#    "drain current (idss@vds,vgs=0)",
    "forward current",
#    "forward voltage (vf@if)",
    "gate trigger current(igt)",
    "hold current",
    "holding current (ih)",
    "idle current",
    "input bias current (ib)",
#    "input current (ii@vi)",
#    "leakage current",
#    "leakage current(dcl)",
    "load current",
    "max output current",
    "maximum charge current",
    "maximum load current",
#    "maximum switching current",
    "maximumcurrent",
    "nominal impulse discharge current",
    "off-state current",
#    "off-state input current (ii(off)@vce,ic)",
    "on-state current (it)",
    "operating current",
#    "output leakage current (icex@vce)",
    "output short circuit current",
    "output sink current",
    "output source current",
    "peak current",
    "peak forward surge current",
#    "peak non-repetitive surge current (itsm@f)",
    "peak output current(sink)",
    "peak output current(source)",
    "pulsed collector current (icm)",
    "quiescent current",
    "quiescent current (ground current)",
    "quiescent current (iq)",
    "quiescent current (max)",
    "rated output current",
    "ratedcurrent",
    "receive  current",
    "receive current",
    "repetitive peak on-state current (itrm)",
#    "reverse leakage current",
#    "reverse leakage current (ir)",
    "sink current",
    "sleep mode current (izz)",
    "source current",
    "standby current",
    "standby current (max)",
    "standby supply current",
    "standby supply current (isb)",
    "steady state current (max)",
    "supply current",
    "supply current (erase)",
    "supply current (icc)",
    "supply current (ipp)",
    "supply current (max)",
    "supply current (program)",
    "supply current (read)",
    "supply current (write)",
    "supply current per channel",
    "supply current(max)",
    "surge current capacity (8/20us)",
    "threshold current",
    "trigger current",
    "trip current",
    "working current"
    ]

capattr = [
    "built-in load capacitance",
#    "diode capacitance",
    "electrostatic capacitance",
    "input capacitance",
    "input capacitance (ci)",
#    "input capacitance (cies@vce)",
#    "junction capacitance(cj)@1mhz",
    "load capacitance",
    "maximum capacitance @ 1mhz",
    "nominal capacitance",
    "off-state capacitance (co)",
    "static capacitance"
    ]

voltsattr = [
    "allowable voltage (ac)",
    "allowable voltage (dc)",
    "applied voltage",
    "zener voltage (nom)",
#    "breakdown voltage",
    "breakdown voltage (vbr)",
    "c-e saturation voltage",
    "voltage rating (max)",
    "charging saturation voltage",
#    "clamp diode forward voltage (vf@if)",
    "clamping voltage@ipp",
    "coil voltage",
    "collector emitter breakdown voltage(vceo)",
    "collector emitter voltage",
#    "collector-emitter   saturation voltage (vce(sat)@ii,ic)",
    "collector-emitter breakdown voltage (vceo)",
    "collector-emitter breakdown voltage (vces)",
#    "collector-emitter saturation voltage (vce(sat)@ic,ib)",
#    "collector-emitter saturation voltage (vce(sat)@ic,if)",
#    "collector-emitter saturation voltage (vce(sat)@ic,vge)",
    "collector-emitter voltage (vceo)",
    "common mode voltage",
#    "forward voltage (vf@if)",
    "control voltage range / center",
    "dc rated voltage",
    "dc reverse voltage",
    "dc spark-over voltage",
#    "diode forward voltage (vf@if)",
#    "dropout voltage",
    "end-off voltage",
    "forward voltage",
    "forward voltage (typ)",
    "forward voltage (vf)",
#    "forward voltage (vf) @ if",
#    "forward voltage (vf@if)",
#    "forward voltage (vf@if)forward current",
    "gate trigger   voltage (vgt)",
#    "gate-emitter threshold voltage (vge(th)@ic)",
    "gate-source breakdown voltage (v(br)gss)",
#    "gate-source cutoff voltage (vgs(off)@id)",
    "input forward voltage",
    "input hysteresis voltage (vhys)",
    "input low voltage",
    "input offset voltage (vos)",
#    "input offset voltage drift (vos tc)",
#    "input voltage",
#    "input voltage (vi(off)@ic,vce)",
#    "input voltage (vi(on)@ic,vce)",
    "input voltage(ac)",
    "input voltage(dc)",
    "input voltage(vac)",
#    "insulated voltage",
    "intput high voltage",
    "isolation voltage",
#    "isolation voltage(rms)",
    "load voltage",
#    "maximum clamping voltage",
    "maximum collector emitter voltage (vceo)",
    "maximum input voltage",
#    "maximum switching voltage",
#    "on-state input   voltage(vi(on)@vce,ic)",
    "on-state voltage (vt)",
    "operating voltage",
    "operating voltage (max)",
    "output high voltage",
    "output low voltage",
#    "output voltage (vo(on)@io/ii)",
    "peak impulse voltage",
    "peak off-state voltage",
    "peak off-state voltage(vdrm)",
#    "ratedvoltage",
    "receiving end voltage",
    "reset voltage",
    "reverse stand-off voltage (vrwm)",
    "reverse voltage",
    "reverse voltage (vr)",
    "supply voltage",
    "supply voltage (vcca)",
    "supply voltage (vccb)",
    "supply voltage(single)",
    "switching voltage (vs)",
    "the power supply voltage",
    "threshold voltage",
    "upply voltage (vcc)",
    "varistor voltage",
    "voltage - input offset(vos)",
    "voltage - load",
    "voltage drop",
    "voltage rating",
    "voltage rating  (ac)",
    "voltage rating (ac)",
    "voltage rating (dc)",
    "voltage rating (max)",
    "voltage(ac)",
#    "withstanding voltage",
    "working voltage",
    "zener voltage (nom)",
#    "zener voltage (range)"
    ]

timeattr = [
    "Propagation delay time"
]