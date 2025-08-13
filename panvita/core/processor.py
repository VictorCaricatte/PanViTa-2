

class GBKProcessor:
    @staticmethod
    def extract_faa(gbk_file):
        """Extract protein sequences from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        final = []
        for i in range(0, len(cds)):
            if "   CDS   " in cds[i]:
                locus_tag = ""
                product = ""
                sequence = []
                
                for j in range(i, len(cds)):
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        
                    elif "/product=" in cds[j]:
                        product = cds[j].replace("/product=", "")
                        product = product.strip()
                        product = product.replace("\"", "")
                        product = product.replace("\n", '')
                        
                    elif "/translation=" in cds[j]:
                        if cds[j].count("\"") == 2:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            final.append(seq)
                            break
                        else:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            sequence.append(seq)
                            k = j + 1
                            if "\"" in cds[k]:
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            else:
                                while ("\"" not in cds[k]):
                                    seq = cds[k].replace(" ", "")
                                    seq = seq.replace("\"", "")
                                    sequence.append(seq)
                                    k = k + 1
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            for l in sequence:
                                final.append(l)
                            break
        return final

    @staticmethod
    def extract_positions(gbk_file):
        """Extract CDS positions from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        positions = {}
        lenght = 0
        totalcds = 0
        
        for i in range(0, len(cds)):
            if ("   CDS   " in cds[i]) and ("   ::" not in cds[i]):
                locus_tag = ""
                position = ""
                
                for j in range(i, len(cds)):
                    if "   CDS   " in cds[j]:
                        totalcds = totalcds + 1
                        position = cds[j].replace('\n', '')
                        position = position.replace("CDS", "")
                        position = position.strip()
                        
                        if (">" in position) or ("<" in position):
                            position = position.replace(">", "").replace("<", "")
                            
                        if "complement(join(" in position:
                            position = position.replace("complement(join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                                    
                        elif "complement(" in position:
                            position = position.replace("complement(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                        elif "join(" in position:
                            position = position.replace("join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                        else:
                            position = position.replace("<", "").replace(">", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
                    elif ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
            if "CONTIG " in cds[i]:
                lenght = lenght + int(cds[i].strip().replace(")", "").split("..")[-1])
                
        return positions

