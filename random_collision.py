import os
import random
import hashlib
import binascii
import datrie
from tqdm import tqdm
import ecdsa
import base58
from feishu_msg import send_feishu_text

chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
TRIE = datrie.Trie(chars)

def load_addresses_to_datrie(filename):
    with open(filename, 'r') as f:
        for line in f:
            addr = line.strip()
            TRIE[addr] = True

# 2. 生成随机私钥（32字节），并转成BTC地址

def private_key_to_wif(priv_key_bytes):
    # WIF格式，前缀0x80 + priv_key + 4 bytes checksum
    extended_key = b'\x80' + priv_key_bytes
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    wif = base58.b58encode(extended_key + checksum)
    return wif.decode()

def private_key_to_public_key(priv_key_bytes):
    sk = ecdsa.SigningKey.from_string(priv_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    # 压缩公钥格式
    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    prefix = b'\x02' if y % 2 == 0 else b'\x03'
    public_key_compressed = prefix + x.to_bytes(32, byteorder='big')
    return public_key_compressed

def public_key_to_address(pub_key_bytes):
    sha256_bpk = hashlib.sha256(pub_key_bytes).digest()
    ripemd160_bpk = hashlib.new('ripemd160', sha256_bpk).digest()
    # 添加版本字节 0x00 for mainnet
    prefixed_ripemd160 = b'\x00' + ripemd160_bpk
    checksum = hashlib.sha256(hashlib.sha256(prefixed_ripemd160).digest()).digest()[:4]
    binary_address = prefixed_ripemd160 + checksum
    address = base58.b58encode(binary_address)
    return address.decode()

def generate_random_priv_key():
    return os.urandom(32)

def main(address_file, try_count=100000):
    print("加载公钥地址到datrie...")
    load_addresses_to_datrie(address_file)
    print(f"共加载{len(TRIE)}个地址")

    if "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo" in TRIE:
        print("测试成功")
    else:
        print("测试失败，请检查地址文件是否正确")

    for _ in tqdm(range(try_count)):
        priv_key = generate_random_priv_key()
        pub_key = private_key_to_public_key(priv_key)
        addr = public_key_to_address(pub_key)

        # 显示私钥和地址
        
        if addr in TRIE:
            wif = private_key_to_wif(priv_key)
            msg = "\n".join([
                f"找到匹配地址: {addr}"
                f"对应私钥(WIF): {wif}",
                f"私钥: {binascii.hexlify(priv_key).decode()}",
                f"公钥(HEX): {binascii.hexlify(pub_key).decode()}",
                f"生成的地址: {addr}"
            ])
            print(msg)

            send_feishu_text("牛逼！找到匹配地址", msg)
            
            break
    else:
        print("未找到匹配的地址。")

if __name__ == '__main__':
    # 替换成你的公钥地址文件路径
    address_txt_file = "./trading_data_cache/addresses.txt"
    main(address_txt_file, try_count=int(1e10))
