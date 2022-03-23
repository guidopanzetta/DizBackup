import os
import time
import pickle
import gzip
import shutil
import yaml

# Il programma crea una backup directory se non esiste
# la prima volta genera index.gz dal dizionario con le absolute path dei file della working directory locale
# le volte successive aggiorna il dizionario e riscrive index.gz
# nella backup directory copia i soli file modificati o nuovi


config = {}
try:
    config = yaml.safe_load(open('C:\\Users\\guido\\Desktop\\Working_Directory\\config.yaml'))
except Exception as ex:
    print(f'Error {ex}')
    exit()

# Working Directory locale = 'C:\\Users\\guido\\Desktop\\Workng_Directory'
workingDir = config['source_dir']

# Backup Directory = 'C:\\Users\\guido\\Desktop\\Backup_Directory'
remoteBackupDir = config['dest_dir']

# Absolute path del file-dizionario (se esistente)
indexFile = remoteBackupDir + "\\index.gz"

# inizializzazione dizionario
index = {}

# verifico se esiste una working directory locale
if os.path.exists(workingDir) and os.path.isdir(workingDir):
    print("\nCartella di lavoro locale " + workingDir)

    # verifica se esiste una backup directory
    if os.path.exists(remoteBackupDir) and os.path.isdir(remoteBackupDir):
        print("\nCartella di Backup " + remoteBackupDir)

        # verifica se esiste un precedente file-dizionario nella backup directory
        if os.path.exists(indexFile) and os.path.isfile(indexFile):
            # apro in lettura il dizionario esistente nella Backup Directory
            try:
                index = pickle.load(gzip.open(indexFile, "rb"))
                # mostra a video il contenuto del dizionario esistente nella Backup Directory
                # print("\nDizionario esistente\n")
                # for elem in index:
                # print(elem, datetime.fromtimestamp(index[elem]).strftime('%Y-%m-%d %H:%M:%S'))

            except IOError as err:
                print(err)
                # print("\nindex = pickle.load(gzip.open(indexFile, rb)) \n")
        else:
            print("\nPrecedente Dizionario non esistente\n")

    else:
        try:
            os.mkdir(remoteBackupDir)
            print("\nHo creato la Backup Directory" + remoteBackupDir)
        except OSError as e:
            print("Error:", e.strerror)
            print("\nImpossibile creare la Backup Directory" + remoteBackupDir)

    # creo la struttura ad albero nella backup directory
    for root, dirs, files in os.walk(workingDir):
        for name in dirs:
            fullpath = os.path.join(root, name)
            # print(fullpath)
            newDir = fullpath.replace(workingDir, remoteBackupDir)
            if not os.path.exists(newDir):
                try:
                    os.mkdir(newDir)
                    # print(newDir)
                except OSError as e:
                    print("Error:", e.strerror)
                    print("\nImpossibile creare la backup subdirectory" + newDir)

    # contatore dei file nuovi o modificati
    n_file_ins = 0

    start = time.time()

    for root, dirs, files in os.walk(workingDir):
        for name in files:
            fullpath = os.path.join(root, name)

            if index.get(fullpath) is None or index[fullpath] < os.path.getmtime(fullpath):
                index[fullpath] = os.path.getmtime(fullpath)
                try:
                    # inserisco il file nuovo o modificato nella cartella di Backup remoto
                    # newfile = fullpath.replace(workingDir, remoteBackupDir)
                    # print(newfile)
                    # dest = os.path.abspath(newfile)
                    # print(newfile)
                    shutil.copy2(fullpath, fullpath.replace(workingDir, remoteBackupDir))
                    n_file_ins = n_file_ins + 1
                except OSError as e:
                    print("Error: %s : %s" % (fullpath, e.strerror))

    print("Tempo di esecuzione  ")
    stop = time.time()
    print(stop - start)

    if n_file_ins > 0:
        try:
            pickle.dump(index, gzip.open(indexFile, "wb"))
            print("\nInseriti nella cartella di Backup ", n_file_ins, " file")
        except IOError as err:
            print(err)
            print("\nErrore in pickle.dump(index, gzip.open(workingDir, wb)) \n")
    else:
        print("\nNon ho inserito alcun file nella Backup Directory")
else:
    print("\nWorking Directory locale non trovata\n")

pass
