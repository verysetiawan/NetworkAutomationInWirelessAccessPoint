#import library flask, paramiko, time, dan modul config router
from flask import Flask, request, jsonify, render_template
import paramiko
import time



#variabel ip (untuk ip yang diremote), username (untuk masuk ssh), password (password ssh)
ip_address_cr = "192.168.88.1"
username_cr = "admin"
password_cr = ""


#Mendeklarasikan app untuk menjalankan flask
app = Flask(__name__,template_folder='template')


#Menambahkan fungsi config
@app.route("/conf", methods=["POST"])
def config():
    #menangkap ip mikrotik client
    data = request.get_json()
    ip_mik = data["ip_router"]
    username = "admin"
    password = ""
    ip_gate = data["ip_gateway"]

    # Cetak ip Mikrotik
    print (f"IP Address Mikrotik adalah : {ip_mik}")
    print (f"IP Gateway Router Klien Mikrotik adalah : {ip_gate[:13]}")
    print (f"host id nya adalah: {ip_mik[11:]}")

    #modulus frequency
    freq = int (ip_mik[11:])
    chanel = freq%3
    
    if chanel == 0 :
        frekuensi = "2412"
    elif chanel == 1 :
        frekuensi = "2437"
    else :
        frekuensi = "2462"
    #print (frekuensi)
    
    #Menyimpan informasi ip ke file ip_address.txt
    file_write = open ("template/ip_address.txt","a")
    file_write.write (ip_mik)
    file_write.write ("\n")
    file_write.close()

    #perintah untuk melakukan koneksi ssh client ke mikrotik
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip_mik,username=username,password=password, allow_agent=False, look_for_keys=False)
    print (f"sukses login to {ip_mik}")
    
    #Perintah konfigurasi router klien     
    config_list = [
        f"/system identity set name=MUM-AP-{ip_mik[11:]}",
        '/interface bridge port remove [find interface="wlan1"]',
        "/tool romon set enabled=yes secrets=mum2020",
        "ip service disable telnet,ftp,www,api-ssl",
        '/interface wireless security-profiles set [ find default=yes ] authentication-types=wpa-psk,wpa2-psk eap-methods="" management-protection=allowed mode=dynamic-keys  wpa-pre-shared-key=smkn1nglegok wpa2-pre-shared-key=smkn1nglegok',
        f'/interface wireless set [ find default-name=wlan1 ] band=2ghz-g/n channel-width=20mhz disabled=no frequency={frekuensi} mode=ap-bridge radio-name=MUM-AP-{ip_mik[11:]} ssid=MUM-AP-{ip_mik[11:]}',
        '/interface wireless access-list add interface=wlan1 signal-range=-80..120 vlan-mode=no-tag',
        f"/ip dns set servers={ip_gate[:13]}",
        f"/ip address add address=172.16.{ip_mik[11:]}.1/27 interface=wlan1 network=172.16.{ip_mik[11:]}.0",
        f'/ip dhcp-relay add dhcp-server=192.168.88.1 disabled=no interface=wlan1 local-address=172.16.{ip_mik[11:]}.1 name=AP-{ip_mik[11:]}',
        #f"/ip dhcp-server network add address=172.16.{ip_mik[11:]}.0/27 dns-server={ip_gate[:13]} gateway=172.16.{ip_mik[11:]}.1",
        "/ip neighbor discovery-settings set discover-interface-list=none",
        "/system ntp client set enabled=yes primary-ntp=202.162.32.12",
        "/system clock set time-zone-name=Asia/Jakarta",
        #"/routing ospf interface add authentication=md5 authentication-key=smkn1nglegok interface=wlan1 network-type=broadcast passive=yes",
        #"/routing ospf interface add authentication=md5 authentication-key=smkn1nglegok interface=bridge network-type=broadcast",
        #f"/routing ospf network add area=backbone network=172.16.{ip_mik[12:]}.0/24",
        #"/routing ospf network add area=backbone network=192.168.100.0/26",
        "tool bandwidth-server set enabled=no",
        "user add name=noc password=noc123 disabled=no group=read",
        "user add name=supervisor password=supervisor123 disabled=no group=write"
        ]

    #Konfigurasi router klien
    for config in config_list:
        ssh_client.exec_command(config)
        print (config)
        time.sleep(0.2)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip_address_cr,username=username,password=password, allow_agent=False, look_for_keys=False)
    print (f"sukses login to {ip_address_cr}")
    rellay_list = [
                    f'/ip pool add name=AP-MUM-{ip_mik[11:]} ranges=172.16.{ip_mik[11:]}.2-172.16.{ip_mik[11:]}.30',
                    f'/ip dhcp-server add address-pool=AP-{ip_mik[11:]} disabled=no interface=bridge lease-time=30m name=AP-{ip_mik[11:]} relay=172.16.{ip_mik[11:]}.1',
                    f'/ip dhcp-server network add address=172.16.{ip_mik[11:]}.0/27 dns-server=8.8.8.8 gateway=172.16.{ip_mik[11:]}.1',
                    f'/queue simple add name=Limit-AP-MUM-{ip_mik[11:]} target=172.16.{ip_mik[11:]}.0/27 queue=pcq-upload-default/pcq-download-default max-limit=15M/15M'
                    ]
    for rellay in rellay_list:
        ssh_client.exec_command(rellay)
        print (rellay)
        time.sleep(0.2)

    print (f"Berhasil menambahkan rellay pada Core Router untuk network 172.16.{ip_mik[11:]}.0/24 ")
    
    return jsonify(data) 


#Menjalankan flask
if __name__ == "__main__":
        app.run (host='0.0.0.0', debug=True, port=5010)
