import helpers as h
import os

def main():
    res = h.generate_results()
    plt = h.plot_results(res)
    tbl = h.get_summary_table(res)

    print(tbl)
    plt.show()

if __name__ == "__main__":
    main()