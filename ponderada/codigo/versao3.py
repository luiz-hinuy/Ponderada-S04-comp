"""A4, versão 3: produtor adquire mutex antes de vazio, provocando deadlock."""

from experimento import principal

if __name__ == "__main__":
    principal(3)
