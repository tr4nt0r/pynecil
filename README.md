# Pynecil

Python library to communicate with Pinecil V2 soldering irons via Bluetooth

[![build](https://github.com/tr4nt0r/pynecil/workflows/Build/badge.svg)](https://github.com/tr4nt0r/pynecil/actions)
[![codecov](https://codecov.io/gh/tr4nt0r/pynecil/graph/badge.svg?token=RM3MC4LP07)](https://codecov.io/gh/tr4nt0r/pynecil)
[![PyPI version](https://badge.fury.io/py/pynecil.svg)](https://badge.fury.io/py/pynecil)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pynecil?style=flat&label=pypi%20downloads)
[!["Buy Me A Coffee"](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/tr4nt0r)
[![GitHub Sponsor](https://img.shields.io/badge/GitHub-Sponsor-blue?logo=github)](https://github.com/sponsors/tr4nt0r)

---

## 📖 Documentation

- **Full Documentation**: [https://tr4nt0r.github.io/pynecil](https://tr4nt0r.github.io/pynecil)
- **Source Code**: [https://github.com/tr4nt0r/pynecil](https://github.com/tr4nt0r/pynecil)

---

## 📦 Installation

You can install Pynecil via pip:

```sh
pip install pynecil
```

## 🚀 Usage

### Basic Example

```python
import asyncio
from pynecil import CharSetting, discover, Pynecil 

async def main():
    
    device = await discover()
    client = Pynecil(device)

    device_info = await client.get_device_info()

    live_data = await client.get_live_data()

    await client.write(CharSetting.SETPOINT_TEMP, 350)

asyncio.run(main())
```

For more advanced usage, refer to the [documentation](https://tr4nt0r.github.io/pynecil).

---

## 🛠 Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes and commit them.
4. Submit a pull request.

Make sure to follow the [contributing guidelines](CONTRIBUTING.md).

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ❤️ Support

If you find this project useful, consider [buying me a coffee ☕](https://www.buymeacoffee.com/tr4nt0r) or [sponsoring me on GitHub](https://github.com/sponsors/tr4nt0r)!
