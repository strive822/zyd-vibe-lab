import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const root=path.dirname(fileURLToPath(import.meta.url));
const lock=path.join(root,'.service-lock.json');
if(fs.existsSync(lock)){
 const state=JSON.parse(fs.readFileSync(lock,'utf8'));
 if(state.root!==root || !Number.isInteger(state.pid) || state.pid<1)throw Error('Invalid service state');
 // Validate the executable and exact launcher command before terminating its tree.
 const ps=`$p=Get-CimInstance Win32_Process -Filter 'ProcessId = ${state.pid}'; if($p -and $p.ExecutablePath -eq '${path.join(root,'runtime','node.exe').replaceAll("'","''")}' -and $p.CommandLine.Contains('${path.join(root,'launcher.mjs').replaceAll("'","''")}')) { Write-Output 'MATCH'; exit 0 } else { exit 4 }`;
 try{
  const checked = execFileSync('powershell.exe',['-NoProfile','-EncodedCommand',Buffer.from(ps,'utf16le').toString('base64')],{windowsHide:true,stdio:'pipe',encoding:'utf8'});
  if (checked.trim() !== 'MATCH') throw Error('Process identity validation failed');
  execFileSync('taskkill.exe', ['/PID',String(state.pid),'/T','/F'], {windowsHide:true,stdio:'pipe'});
  if(fs.existsSync(lock))fs.unlinkSync(lock);
  console.log('LibreTV stopped.');
 }catch(e){if(e.status===4){fs.unlinkSync(lock);console.log('No matching LibreTV process; stale lock removed.');}else throw e;}
}else console.log('LibreTV is not running.');
