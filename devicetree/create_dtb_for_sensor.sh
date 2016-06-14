#!/bin/sh -x
install_dtc() {
  #sh -x ./dtc-overlay.sh
  cd  /root/devicetree/dtc
  make PREFIX=/usr/local/ CC=gcc CROSS_COMPILE= all
  echo "Installing into: /usr/local/bin/"
  make PREFIX=/usr/local/ install
  echo "dtc: `/usr/local/bin/dtc --version`"
}
install_dtc

build_dtb() {
    cd  /root/devicetree/
    git clone https://github.com/RobertCNelson/dtb-rebuilder.git
    git checkout origin/4.0.x
    cd /root/devicetree/dtb-rebuilder
    cp /root/devicetree/P9-15-pull-up.dtsi src/arm/
    #cp /root/devicetree/am335x-cape-rtc-ds1307.dtsi src/arm/
    cp /root/devicetree/i2c-1.dtsi src/arm/
    git clone https://github.com/beagleboard/bb.org-overlays
    cd bb.org-overlays
    git checkout 56390f91e6e1977e3829af638075845dd70c44aa
    cd ..
    [ ! -f 'src/arm/am335x-boneblack.dts' ] && echo 'Missing src/arm/am335x-boneblack.dts' && exit 1
    cat << EOF >>'src/arm/am335x-boneblack.dts'
include "P9-15-pull-up.dtsi"
include "am335x-cape-rtc-ds1307.dtsi"
include "i2c-1.dtsi"
EOF

    make
}
build_dtb
/bin/cp src/arm/am335x-boneblack.dtb /boot/dtbs/
