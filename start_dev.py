#!/usr/bin/env python3
import asyncio
from utils.start_dev import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário") 