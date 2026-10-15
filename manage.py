"""Local backup/recovery utility. Never starts a public server."""
import argparse
import json
import sqlite3
from pathlib import Path
import zipfile
from harvest.business import (bundle,current_revision,load_version,list_versions,save_version,workspace_backup)


def main():
    parser=argparse.ArgumentParser(description='CEBAFEX local workspace backup and recovery')
    parser.add_argument('--database',type=Path,default=Path(__file__).parent/'data/cebafex.sqlite3')
    actions=parser.add_subparsers(dest='action',required=True)
    backup=actions.add_parser('backup');backup.add_argument('output',type=Path)
    complete=actions.add_parser('backup-all');complete.add_argument('output',type=Path)
    restore=actions.add_parser('restore');restore.add_argument('archive',type=Path)
    restore.add_argument('--replace-current',action='store_true',required=True,
                         help='Explicitly import this backup as the newest workspace version')
    args=parser.parse_args()
    try:
        if args.action=='backup-all':
            from harvest.operations import database_backup
            if not args.database.is_file():raise ValueError('Database does not exist.')
            with args.output.open('xb') as file:file.write(database_backup(args.database))
            print('Complete SQLite backup created:',args.output)
        elif args.action=='backup':
            versions=list_versions(args.database,1)
            if not versions:raise ValueError('Save a workspace version in the app first.')
            state=load_version(args.database,versions[0]['revision'])
            data=workspace_backup(state)
            with args.output.open('xb') as file:file.write(data)
            print('Backup created:',args.output)
        else:
            if args.archive.stat().st_size>50*1024*1024:raise ValueError('Backup exceeds 50 MB.')
            with zipfile.ZipFile(args.archive) as archive:
                files=archive.infolist()
                matches=[file for file in files if file.filename=='workspace.json']
                if len(matches)!=1 or matches[0].file_size>50*1024*1024:
                    raise ValueError('Backup must contain one workspace.json of at most 50 MB.')
                state=json.loads(archive.read(matches[0]))
            if not isinstance(state,dict) or state.get('schema_version')!=1:raise ValueError('Unsupported backup schema.')
            # Validates every canonical dataset and planning rule before any write.
            import pandas as pd
            for key in ['active_data','active_buyers']:
                if state.get(key) is not None:state[key]=pd.DataFrame(state[key])
            for kind in ['agriculture','buyers']:
                meta=state.get(kind+'_metadata')
                if meta and (not isinstance(meta,dict) or meta.get('origin') not in ['sample','uploaded','manual']):
                    raise ValueError('Unsupported record provenance.')
            bundle(state)
            revision=save_version(state,args.database,'Restored backup',current_revision(args.database))
            print('Backup imported as version',revision)
            print('Open the app and restore the latest saved workspace.')
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error,zipfile.BadZipFile) as exc:
        parser.exit(1,'Recovery error: '+str(exc)+'\n')

if __name__=='__main__':main()
