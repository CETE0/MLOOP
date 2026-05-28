#!/bin/bash -e

install -d -m 0755 "${ROOTFS_DIR}/opt/mloop/src"
install -d -m 0755 "${ROOTFS_DIR}/etc/mloop"
install -d -m 0755 "${ROOTFS_DIR}/var/lib/mloop"
install -d -m 0755 "${ROOTFS_DIR}/home/mloop/media"

if ! chroot "${ROOTFS_DIR}" id -u mloop >/dev/null 2>&1; then
    chroot "${ROOTFS_DIR}" useradd --system --create-home mloop
fi

rsync -a "${STAGE_DIR}/00-install-mloop/files/mloop/" "${ROOTFS_DIR}/opt/mloop/src/"

if [ -d "${STAGE_DIR}/00-install-mloop/files/media" ]; then
    rsync -a "${STAGE_DIR}/00-install-mloop/files/media/" "${ROOTFS_DIR}/home/mloop/media/"
fi

cp "${ROOTFS_DIR}/opt/mloop/src/config/mloop.example.toml" "${ROOTFS_DIR}/etc/mloop/config.toml"
cp "${ROOTFS_DIR}/opt/mloop/src/packaging/systemd/mloop.service" \
    "${ROOTFS_DIR}/etc/systemd/system/mloop.service"

on_chroot <<'EOF'
python3 -m venv /opt/mloop/venv
/opt/mloop/venv/bin/pip install --no-cache-dir /opt/mloop/src
ln -sf /opt/mloop/venv/bin/mloopd /usr/bin/mloopd
chown -R mloop:mloop /opt/mloop /home/mloop/media /var/lib/mloop
systemctl enable mloop
EOF
