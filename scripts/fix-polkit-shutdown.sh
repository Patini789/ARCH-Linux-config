#!/bin/bash
mkdir -p /etc/polkit-1/rules.d

cat << 'CONFIG' > /etc/polkit-1/rules.d/10-enable-shutdown.rules
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.login1.power-off" ||
         action.id == "org.freedesktop.login1.power-off-multiple-sessions" ||
         action.id == "org.freedesktop.login1.power-off-ignore-inhibit" ||
         action.id == "org.freedesktop.login1.reboot" ||
         action.id == "org.freedesktop.login1.reboot-multiple-sessions" ||
         action.id == "org.freedesktop.login1.reboot-ignore-inhibit" ||
         action.id == "org.freedesktop.login1.suspend" ||
         action.id == "org.freedesktop.login1.hibernate") &&
        subject.isInGroup("wheel")) {
        return polkit.Result.YES;
    }
});
CONFIG

systemctl restart polkit
echo "Reglas de Polkit aplicadas. CanPowerOff y CanReboot habilitados."
