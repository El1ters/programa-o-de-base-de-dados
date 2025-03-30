#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors
    /Bernardo Carvalho:
        student1 contribution (%):
        contribution description:
            
    67825/Inês Lopes:
        student2 contribution (%):
        contribution description:

"""

# %%
# MODULES
#


import sqlite3
import math
import matplotlib.pyplot as plt


# %%
# CREATE TABLES
#
def cmd_create_tables(con: sqlite3.Connection):
    """
    Esta função elimina as duas tabelas da base de dados, caso existam.
    Seguidamente, cria duas tabelas vazias na base de dados: Tests e Samples.
    """

    
    con.execute('DROP TABLE IF EXISTS Tests')
    con.execute('DROP TABLE IF EXISTS Samples')
        
    con.execute('''CREATE TABLE Tests(
                id INTEGER,
                mat_id VARCHAR(6),
                year INTEGER,
                temp_ini REAL,
                certification VARCHAR(20),
                PRIMARY KEY(id))''')
    
    con.execute('''CREATE TABLE Samples(
                id INTEGER,
                test_id INTEGER,
                time INTEGER,
                temperature REAL,
                PRIMARY KEY(id))''')
    
    con.commit()
                            

# %%
# LOAD ONE TEST
#
def cmd_load_test(db: sqlite3.Connection, nomeF: str):
    """
    Esta função lê os ficheiros e carrega a informação para as tabelas da 
    base de dados.
       nomeF: nome do ficheiro de teste
    """
    
    header = 1
    tests = []
    samples = []
    try:  
        f = open(nomeF, 'r')
    except:
        print("failed to open file",nomeF)
        return
    
    local = f.readline().strip()
    tests.append(local)
    for linha in f.readlines():
        if header < 5:
            tests.append(linha.strip())
        else:
            samples.append(linha.strip().split(';'))
        header = header + 1
    ensaio = tests[0]
    f.close()
    sql_test = ('INSERT INTO Tests VALUES(?,?,?,?,?);')
    db.execute(sql_test,(tests[0],tests[2],tests[1],tests[4],tests[3]))
    for i in samples:
        sql_samp = ('INSERT INTO Samples VALUES(?,?,?,?);')
        db.execute(sql_samp,(i[0],ensaio,i[1],i[2]))
    
    db.commit()
        
# %%
# WRITE A SUMMARY
#
def cmd_summary(con: sqlite3.Connection, args : str):
    """
    docstring
    """
    try:
        start, end, certification = args.split(';')
    except:
        print("Invalid arguments")
        return
    
    #ir buscar is ids dos materiais que estão entre start e end e que têm a certificação
    start_aux = start
    end_aux = end
    if start == '*':
        sqlcmd = 'SELECT MIN(year) FROM Tests;'
        k = con.execute(sqlcmd)
        n = k.fetchall()
        start_aux = n[0][0]
        
    if end == '*':
        sqlcmd = 'SELECT MAX(year) FROM Tests;'
        k = con.execute(sqlcmd)
        n = k.fetchall()
        end_aux = n[0][0]
        
    # ignorar a certificação
    if certification == '*':
        sqlcmd = 'SELECT id, mat_id FROM Tests WHERE year >= ? AND year <= ?;'
        k = con.execute(sqlcmd,(start_aux,end_aux))
        n = k.fetchall()
        ids = [i[0] for i in n]
        mat_ids = [i[1] for i in n]
    else:
        sqlcmd = 'SELECT id, mat_id FROM Tests WHERE year >= ? AND year <= ? AND certification = ?;'
        k = con.execute(sqlcmd,(start_aux,end_aux,certification))
        n = k.fetchall()
        ids = [i[0] for i in n]
        mat_ids = [i[1] for i in n]
        
    count = 0
    #ir buscar o número de amostras para cada material, percorrer o id da amostra e saber quantas amostras tem
    for i in ids:
        sqlcmd2 = 'SELECT count(*) FROM Samples WHERE test_id = ?;'
        k = con.execute(sqlcmd2,(i,))
        n = k.fetchall()
        count = count + n[0][0]
    
    #escrever no terminal
    
    print("%d materials between %s and %s with certification %s :" % (len(ids),start,end,certification))
    for i in mat_ids:
        print("\t%s" % (i)) 
    print("Total samples: %d" % (count))
    con.commit()
    

def cmd_summary_file(con: sqlite3.Connection, args: str):
    """
    docstring
    """
    try:
        args = args.split(';')
    except:
        print("Invalid arguments")
        return
    filename = args[0]
    args.pop(0)
    f = open(filename, 'w')

    start = args[0] 
    end = args[1]
    certification = args[2]
    #ir buscar is ids dos materiais que estão entre start e end e que têm a certificação
    start_aux = start
    end_aux = end
    if start == '*':
        sqlcmd = 'SELECT MIN(year) FROM Tests;'
        k = con.execute(sqlcmd)
        n = k.fetchall()
        start_aux = n[0][0]
        
        
    if end == '*':
        sqlcmd = 'SELECT MAX(year) FROM Tests;'
        k = con.execute(sqlcmd)
        n = k.fetchall()
        end_aux = n[0][0]
    
    # ignorar a certificação
    if certification == '*':
        sqlcmd = 'SELECT id, mat_id FROM Tests WHERE year >= ? AND year <= ?;'
        k = con.execute(sqlcmd,(start_aux,end_aux))
        n = k.fetchall()
        ids = [i[0] for i in n]
        mat_ids = [i[1] for i in n]
    else:
        sqlcmd = 'SELECT id, mat_id FROM Tests WHERE year >= ? AND year <= ? AND certification = ?;'
        k = con.execute(sqlcmd,(start_aux,end_aux,certification))
        n = k.fetchall()
        ids = [i[0] for i in n]
        mat_ids = [i[1] for i in n]
    
    count = 0
    #ir buscar o número de amostras para cada material, percorrer o id da amostra e saber quantas amostras tem
    for i in ids:
        sqlcmd2 = 'SELECT count(*) FROM Samples WHERE test_id = ?;'
        k = con.execute(sqlcmd2,(i,))
        n = k.fetchall()
        count = count + n[0][0]
    
    #escrever no ficheiro    
    f.write("%d materials between %s and %s with certification %s :\n" % (len(ids),start,end,certification))
    for i in mat_ids:
        f.write("\t%s\n" % (i))
    f.write("Total samples: %d\n" % (count))
    con.commit()
    

# %%
# PLOT A GRAPH OF MATERIALS
#    
def cmd_plot(db: sqlite3.Connection, reference: str ):
    """
    Esta função cria um gráfico com todos os pontos obtidos para o material
    indicado e desenha uma linha que represente o arrefecimento segundo a 
    lei de Newton.
       eixo das abcissas: tempo (tn)
       eixo das ordenadas: temperatura relativa (Tn)
       
         em que Tn = temperatura da amostra / temperatura inicial
       
    Para cada material, utiliza como pontos as diferentes amostras desse material.
    
    As variáveis do gráfico são obtidas através das tabelas da base de dados 
    Tests e Samples:
        tempo - time
        temperatura da amostra - temperature
        temperatura inicial - temp_ini
    """
    try:
        reference = reference.split(';')
    except:
        print("Invalid arguments")
        return
    
    plt.figure()
    plt.title('Cooling over time')
    plt.xlabel('Elapsed time (hours)')
    plt.ylabel('Relative temperature ')
    
    
    for references in reference:
        sqlcmd = 'SELECT id,temp_ini FROM Tests WHERE mat_id = ?;'
        cur = db.execute(sqlcmd,(references,))
        dados = cur.fetchall()
        x = []
        y = []
        #i corresponde ao id da amostra e o k ao temp_ini da amostra
        for i,k in dados:
            sqlcmd2 = 'SELECT time,temperature FROM Samples WHERE test_id = ? ORDER BY time;'
            cur = db.execute(sqlcmd2,[i])
            res = cur.fetchall()
            normalized_data = [(time, round(temp / k,3)) for time, temp in res]
            for i in normalized_data:
                x.append(i[0])
                y.append(i[1])
                
        s = 0
        N = len(normalized_data[1])
        for i in range(N):
            s = s + (-math.log(y[i]))/x[i]
            cons = s / N

        abs = [a for a in range(1,100)]
        ord = [math.e**(- cons * b) for b in abs]
        plt.plot(x,y,'x')
        plt.plot(abs,ord, label = references)
    plt.legend() 
    plt.show()


# %%
# PLOT A GRAPH TO FILE
#


def cmd_plot_file(db: sqlite3.Cursor, args: str):
    """
    Esta função guarda o gráfico no ficheiro com o nome em nomeF.
    """
    try:
        args = args.split(';')
    except:
        print("Invalid arguments")
        return
    filename = args[0]
    args.pop(0)
    
    plt.figure()
    plt.title('Cooling over time')
    plt.xlabel('Elapsed time (hours)')
    plt.ylabel('Relative temperature ')
    
    
    for references in args:
        sqlcmd = 'SELECT id,temp_ini FROM Tests WHERE mat_id = ?;'
        cur = db.execute(sqlcmd,(references,))
        dados = cur.fetchall()
        x = []
        y = []
        #i corresponde ao id da amostra e o k ao temp_ini da amostra
        for i,k in dados:
            sqlcmd2 = 'SELECT time,temperature FROM Samples WHERE test_id = ? ORDER BY time;'
            cur = db.execute(sqlcmd2,[i])
            res = cur.fetchall()
            normalized_data = [(time, round(temp / k,3)) for time, temp in res]
            for i in normalized_data:
                x.append(i[0])
                y.append(i[1])
                
        s = 0
        N = len(normalized_data[1])
        for i in range(N):
            s = s + (-math.log(y[i]))/x[i]
            cons = s / N

        abs = [a for a in range(1,100)]
        ord = [math.e**(- cons * b) for b in abs]
        plt.plot(x,y,'x')
        plt.plot(abs,ord, label = references)
    plt.legend() 
    plt.savefig(filename)


# %%
# EXECUTE ONE COMMAND
#
def cmd_execute(con: sqlite3.Connection, args: str):
    """
    docstring
    """
    try:  
        f = open(args, 'r')
    except:
        print("failed to open file",args)
        return
    
    line = f.readline().strip()
    
    while line != '':
        process_one_cmd(con, line) 
        line = f.readline().strip()
    f.close()


# %%
# AUXILIAR FUNCTIONS
#

def strip_list(x: list[str]) -> list[str]:
    """
    Strip all the strings in the list
    """
    return [i.strip() for i in x]

def upper_command(s: str) -> str:
    """
    Converts the first word in 's' to uppercase.
    """
    words = strip_list(s.split(' ', maxsplit=1))
    words[0] = words[0].upper()
    cmd = ' '.join(words)
    return cmd


def read_command(f):
    """
    Reads a command.
    retuns the command word in uppercase followed by the given arguments.
    """
    if f is None:
        # reads from keyboard
        cmd = ''
        while cmd == '':
            cmd = input("Command: ").strip()
    else:
        # reads from file 'f'
        cmd = f.readline()
        if cmd == '':
            cmd = 'QUIT'
    return upper_command(cmd.strip())


# %%
# PROCESS ONE COMMAND
#
def process_one_cmd(db: sqlite3.Connection, comando: str):
    """
    docstring
    """
    comando = comando + ' '
    cmd = strip_list(comando.split(' ', 1))
    cmd[0] = cmd[0].upper()
    if cmd == 'QUIT':
        pass   # really nothing to do!
    elif cmd[0] == 'CREATE_TABLES':
        cmd_create_tables(db)
    elif cmd[0] == "LOAD_TEST":
        try:
            cmd[1] = cmd[1].split(";")
        except:
            print("Invalid arguments")
            return
        for i in cmd[1]:
            cmd_load_test(db, i)
    elif cmd[0] == "SUMMARY":
        cmd_summary(db, cmd[1])
    elif cmd[0] == "SUMMARY_FILE":
        cmd_summary_file(db, cmd[1])
    elif cmd[0] == "PLOT":
        cmd_plot(db, cmd[1])
    elif cmd[0] == "PLOT_FILE":
        cmd_plot_file(db, cmd[1])
    elif cmd[0] == "SUMMARY":
        cmd_summary_file(db, cmd[1])
    elif cmd[0] == "EXECUTE":
        cmd_execute(db, cmd[1])
    else:
        print('Unknown command!')
    return None


# %%
# MAIN FUNTION TO PROCESS ALL COMMANDS
#

def process_cmds(db_file: str, inf=None):
    """
     Processes a sequence of commands, producing corresponding outputs.
     db_file: name of the database where to place/read the information.
     inf: (please ignore, call this function with only the first argument)
    """
    assert (db_file != "")

    #   open the database file
    conn = sqlite3.connect(db_file)

    # The main loop
    cmd = '#'
    while cmd != 'QUIT':
        if cmd != '#':
            process_one_cmd(conn, cmd)
        cmd = read_command(inf)

    conn.close()
    print("BYE!")


def main():
    process_cmds("BDacademica.db")


if __name__ == '__main__':
    main()  # run program
