with open("data/nodes.csv", "r", newline="") as infile, open("nodes_fixed.csv", "w", newline="\n") as outfile:
    for line in infile:
        outfile.write(line.replace("\r\n", "\n"))

print("Fixed CSV saved as nodes_fixed.csv")
