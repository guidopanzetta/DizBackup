import os
from datetime import datetime
import pickle
import gzip
import shutil
import yaml

# Il programma crea una cartella di backup remoto se non esiste
# la prima volta genera index.gz dal dizionario con i nomi dei file della cartella di lavoro locale
# le volte successive aggiorna il dizionario e riscrive index.gz
# nella cartella di backup crea una sottocartella (con data e ora di esecuzione) contenente
# i soli file modificati o nuovi da condividere (NON SO SE E' UTILE... SE MAI LA TOLGO)
# nella cartella di backup locale sono presenti tutti i file nuovi, aggiornati e anche quelli vecchi
# NON SO SE QUESTA ERA LA LOGICA DELL'APPLICAZIONE
# manca la parte per caricare il file s server remoto che per ora è manuale

config = {}
try:
    config = yaml.safe_load(open('config.yaml'))
except Exception as ex:
    print(f'Error {ex}')
    exit()

# cartella di lavoro locale
workingDir = config['source_dir']
# cartella di destinazione del backup remoto INSERIRE !!!!
remoteBackupDir = config['dest_dir']
# nome del file-dizionario
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
                # stampa il dizionario esistente nella cartella di Backup remoto
                print("\nDizionario esistente\n")
                for elem in index:
                    print(elem, datetime.fromtimestamp(index[elem]).strftime('%Y-%m-%d %H:%M:%S'))
            except IOError as err:
                print(err)
                print("\nindex = pickle.load(gzip.open(indexFile, rb)) \n")
        else:
            print("\nPrecedente Dizionario non esistente\n")
    else:
        try:
            os.mkdir(remoteBackupDir)
            print("\nHo creato la cartella remota di Backup " + remoteBackupDir)
        except OSError as e:
            print("Error:", e.strerror)
            print("\nCan't create remote backup subdirectory" + remoteBackupDir)

    # inizializazione del nome sottocartella di backup
    dataeora = datetime.now()
    backupFolder = remoteBackupDir + "\\Backup" + dataeora.strftime("%Y-%m-%d_%H-%M-%S")

    if not os.path.exists(backupFolder):
        try:
            # creazione sottocartella di backup per i soli file nuovi o modificati
            os.mkdir(backupFolder)
            print("\nCreazione sottocartella di backup " + backupFolder)

            # inizializzazione contatore dei file presenti nella cartella di lavoro locale
            n_file_p = 0
            # inizializzazione contatore dei file modificati o inseriti nel dizionario esistente
            n_file_ins = 0

            # esplorazione della cartella di lavoro
            for root, dirs, files in os.walk(workingDir):

                for f in files:
                    fullpath = os.path.join(root, f)

                    # aggiornamento contatore file presenti nella cartella di lavoro
                    n_file_p = n_file_p + 1

                    # controllo se esiste nel dizionario la chiave-file
                    if index.get(fullpath) is None:
                        index[fullpath] = os.path.getmtime(fullpath)
                        try:
                            # inserisco il  file nuovo o modificato nella cartella di Backup remoto
                            shutil.copy(fullpath, remoteBackupDir)
                            # inserisco il  file nuovo o modificato nella sottocartella di Backup remoto
                            shutil.copy(fullpath, backupFolder)
                            print("inserito ", fullpath, datetime.fromtimestamp(index[fullpath]).strftime('%Y-%m-%d %H:%M:%S'))
                            n_file_ins = n_file_ins + 1
                        except OSError as e:
                            print("Error: %s : %s" % (fullpath, e.strerror))
                    elif index[fullpath] < os.path.getmtime(fullpath):
                        try:
                            oldFile = remoteBackupDir + "\\" + f
                            nameOld = oldFile + datetime.fromtimestamp(index[fullpath]).strftime('%Y-%m-%d %H-%M-%S') + ".old"
                            try:
                                os.rename(oldFile, nameOld)
                            except OSError as e:
                                print("Error: %s : %s" % (fullpath, e.strerror))

                            shutil.copy(fullpath, remoteBackupDir)
                            shutil.copy(fullpath, backupFolder)
                            print("aggiornato ", fullpath, datetime.fromtimestamp(index[fullpath]).strftime('%Y-%m-%d %H:%M:%S'))
                            index[fullpath] = os.path.getmtime(fullpath)
                            n_file_ins = n_file_ins + 1
                        except OSError as e:
                            print("Error: %s : %s" % (fullpath, e.strerror))
            if n_file_p > 0:
                try:
                    pickle.dump(index, gzip.open(indexFile, "wb"))
                    print("\nScrittura del dizionario nuovo o aggiornato\n")

                    if n_file_ins > 0:
                        print("\nInseriti nella cartella di Backup ", n_file_ins, " file")
                    else:
                        print("\nNon ho inserito alcun file nella sottocartella di Backup")

                except IOError as err:
                    print(err)
                    print("\nErrore in pickle.dump(index, gzip.open(workingDir, wb)) \n")
            else:
                print("\nNon ci sono file nella cartella di lavoro locale\n")
        except OSError as err:
            print(err)
            print("\nCan't create backup subdirectory" + backupFolder)
    else:
        print("\nSottocartella di backup già esistente\n")
else:
    print("\nCartella di lavoro locale non trovata\n")

pass
