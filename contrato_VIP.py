#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 19:27:20 2025
@author: hugotrejo
"""

import streamlit as st
from web3 import Web3
import requests
import datetime

# --------------------------
# Configuración de conexión
# --------------------------
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Carga dinámica del contrato
contract_address_input = st.text_input("📍 Dirección del contrato desplegado:", value="0x65B8634d1f2E431c40d501Fd74095950d6Ae83A0")
contract_address = Web3.to_checksum_address(contract_address_input)

# Input del usuario
address = st.text_input("👤 Tu dirección Ethereum:")
private_key = st.text_input("🔑 Clave privada (solo si eres el owner o vas a firmar)", type="password")

# --------------------------
# Cargar ABI desde IPFS
# --------------------------
IPFS_CID = "QmTuPcAnrGG9PZXMAegCJ5Y6mqjqiAYs4hrDG2PzHnEEkn"
ipfs_url = f"https://ipfs.io/ipfs/{IPFS_CID}"

try:
    response = requests.get(ipfs_url)
    response.raise_for_status()
    abi = response.json()["abi"]
except Exception as e:
    st.error(f"Error al cargar el ABI desde IPFS: {e}")
    st.stop()

# Instancia del contrato
contract = web3.eth.contract(address=contract_address, abi=abi)

# --------------------------
# Interfaz principal
# --------------------------
st.title("🎫 Compra de Boletos VIP para Conciertos")
st.caption("Interacción con contrato inteligente en Ganache")

menu = st.sidebar.selectbox("Menú", ["Comprar Boleto", "Ver Boletos", "Retirar Fondos"])

# --------------------------
# Comprar boleto
# --------------------------
if menu == "Comprar Boleto":
    artista = st.selectbox("🎤 Artista", ["Taylor Swift", "Bad Bunny", "The Weeknd"])
    fecha = st.date_input("📅 Fecha del concierto", min_value=datetime.date.today())
    precio = contract.functions.precioBoleto().call()
    st.write(f"💸 Precio del boleto: {web3.from_wei(precio, 'ether')} ETH")

    if st.button("Comprar"):
        try:
            account = web3.eth.account.from_key(private_key)
            nonce = web3.eth.get_transaction_count(address)
            tx = contract.functions.comprarBoleto(artista, str(fecha)).build_transaction({
                'from': address,
                'value': precio,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei'),
            })
            signed_tx = account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            st.success(f"✅ Boleto comprado. Tx Hash: `{tx_hash.hex()}`")
        except Exception as e:
            st.error(f"❌ Error al comprar boleto: {e}")

# --------------------------
# Ver boletos
# --------------------------
elif menu == "Ver Boletos":
    if st.button("Consultar"):
        try:
            boletos = contract.functions.boletosUsuario(address).call()
            if boletos:
                for b in boletos:
                    st.write(f"🎤 {b[0]} | 📅 {b[1]} | 💰 {web3.from_wei(b[2], 'ether')} ETH")
            else:
                st.info("No tienes boletos comprados.")
        except Exception as e:
            st.error(f"Error al consultar boletos: {e}")

# --------------------------
# Retirar fondos (owner)
# --------------------------
elif menu == "Retirar Fondos":
    try:
        owner = contract.functions.owner().call()
        if address.lower() == owner.lower():
            if st.button("Retirar Fondos"):
                account = web3.eth.account.from_key(private_key)
                nonce = web3.eth.get_transaction_count(address)
                tx = contract.functions.retirarFondos().build_transaction({
                    'from': address,
                    'nonce': nonce,
                    'gas': 200000,
                    'gasPrice': web3.to_wei('20', 'gwei'),
                })
                signed_tx = account.sign_transaction(tx)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                st.success(f"✅ Fondos retirados. TX Hash: `{tx_hash.hex()}`")
        else:
            st.warning("⚠️ Solo el owner puede retirar fondos.")
    except Exception as e:
        st.error(f"Error al retirar fondos: {e}")
