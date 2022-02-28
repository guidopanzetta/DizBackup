import os
from datetime import datetime
import pickle
import gzip
import shutil
import yaml

# Il programma grea una cartella di backup remoto se non esiste
# la prima volta genera index.gz dal dizionario con i nomi dei file della cartella di lavoro locale
# le volte successive aggiorna il dizionario e riscrive index.gz
# nella cartella di backup copia i soli file modificati o nuovi da condividere

# cartella di lavoro locale workingDir = 'C:\\Users\\guido\\Desktop\\Miacartella'

config = {}
try:
    config = yaml.safe_load(open('C:\\Users\\guido\\Desktop\\Miacartella\\config.yaml'))
except Exception as ex:
    print(f'Error {ex}')
    exit()

# cartella di lavoro locale
workingDir = config['source_dir']

# cartella di destinazione del backup = 'C:\\Users\\guido\\Desktop\\RemoteBackup'
remoteBackupDir = config['dest_dir']

# cartella di destinazione del backup incrementale = 'C:\\Users\\guido\\Desktop\\IncBackupDir'
incBackupDir = 'C:\\Users\\guido\\Desktop\\IncBackupDir'

# nome del file-dizionario (se esistente)
indexFile = remoteBackupDir + "\\index.gz"

# inizializzazione dizionario
index = {}

# verifico se esiste una cartella di lavoro locale
if os.path.exists(workingDir) and os.path.isdir(workingDir):
    print("\nCartella di lavoro locale " + workingDir)

    # verifico se esiste una cartella di backup remoto
    if os.path.exists(remoteBackupDir) and os.path.isdir(remoteBackupDir):
        print("\nCartella di Backup " + remoteBackupDir)

        # verifico se esiste un precedente file-dizionario nella cartella di backup remoto
        if os.path.exists(indexFile) and os.path.isfile(indexFile):
            # apre in lettura il dizionario esistente nella cartella di Backup remoto
            try:
                index = pickle.load(gzip.open(indexFile, "rb"))
                # mostra a video il contenuto del dizionario esistente nella cartella di Backup remoto
                print("\nDizionario esistente\n")
                for elem in index:
                    print(elem, datetime.fromtimestamp(index[elem]).strftime('%Y-%m-%d %H:%M:%S'))
            except IOError as err:
                print(err)
                # print("\nindex = pickle.load(gzip.open(indexFile, rb)) \n")
        else:
            print("\nPrecedente Dizionario non esistente\n")
    else:
        try:
            os.mkdir(remoteBackupDir)
            print("\nHo creato la cartella remota di Backup " + remoteBackupDir)
        except OSError as e:
            print("Error:", e.strerror)
            print("\nCan't create remote backup subdirectory" + remoteBackupDir)

    if os.path.exists(incBackupDir) and os.path.isdir(incBackupDir):
        print("\nCartella di Backup Incrementale" + incBackupDir)
    else:
        try:
            os.mkdir(incBackupDir)
            print("\nHo creato la cartella remota di Backup Incrementale " + incBackupDir)
        except OSError as e:
            print("Error:", e.strerror)
            print("\nImposibile creare la cartella di Backup incrementale " + incBackupDir)
            remoteIncrBackupDir = incBackupDir

    # inizializazione del nome sottocartella di backup incrementale
    dataeora = datetime.now()
    incBackupFolder = incBackupDir + "\\Backup" + dataeora.strftime("%Y-%m-%d_%H-%M-%S")

    if not os.path.exists(incBackupFolder):
        try:
            # creazione sottocartella di backup per i soli file nuovi o modificati
            os.mkdir(incBackupFolder)
            print("\nCreazione sottocartella di backup " + incBackupFolder)
        except OSError as err:
            print(err)
            print("\nCan't create backup subdirectory" + incBackupFolder)

        # inizializzazione contatore dei file modificati o inseriti nel dizionario
    n_file_ins = 0

    # creo la struttura ad albero nella cartella di backup e nella cartella di backup incrementale
    for root, dirs, files in os.walk(workingDir):
        for name in dirs:
            fullpath = os.path.join(root, name)
            # print(fullpath)
            newDir = fullpath.replace(workingDir, remoteBackupDir)
            newIncDir = fullpath.replace(workingDir, incBackupFolder)
            if not os.path.exists(newDir):
                try:
                    os.mkdir(newDir)
                    print(newDir)
                except OSError as e:
                    print("Error:", e.strerror)
                    print("\nCan't create remote backup subdirectory" + newDir)
            if not os.path.exists(newIncDir):
                try:
                    os.mkdir(newIncDir)
                    print(newIncDir)
                except OSError as e:
                    print("Error:", e.strerror)
                    print("\nCan't create remote backup subdirectory" + newIncDir)

    for root, dirs, files in os.walk(workingDir):
        for name in files:
            fullpath = os.path.join(root, name)
            if index.get(fullpath) is None or index[fullpath] < os.path.getmtime(fullpath):
                index[fullpath] = os.path.getmtime(fullpath)
                try:
                    # inserisco il file nuovo o modificato nella cartella di Backup remoto e Backup incrementale
                    newfile = fullpath.replace(workingDir, remoteBackupDir)
                    dest = os.path.abspath(newfile)
                    print(dest)
                    shutil.copy(fullpath, dest)
                    newIncfile = fullpath.replace(workingDir, incBackupFolder)
                    dest2 = os.path.abspath(newIncfile)
                    print(dest2)
                    shutil.copy(fullpath, dest2)
                    n_file_ins = n_file_ins + 1
                except OSError as e:
                    print("Error: %s : %s" % (fullpath, e.strerror))

    if n_file_ins > 0:
        try:
            pickle.dump(index, gzip.open(indexFile, "wb"))
            # print("\nScrittura del dizionario nuovo o aggiornato\n")
            print("\nInseriti nella cartella di Backup ", n_file_ins, " file")
        except IOError as err:
            print(err)
            print("\nErrore in pickle.dump(index, gzip.open(workingDir, wb)) \n")
    else:
        print("\nNon ho inserito alcun file nella sottocartella di Backup")
else:
    print("\nCartella di lavoro locale non trovata\n")

pass
