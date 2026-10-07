"""Regression coverage for data preservation, CLI routing, QA, patching and distribution."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import time
import urllib.request
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/tools'))
import qa
import fix_word
import share
import wajs
import whisper_compat
import env_config


def load_cli():
    spec=importlib.util.spec_from_file_location('cli',ROOT/'kit/cli.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='wvf-test-')
        self.addCleanup(self.temp.cleanup)
        self.tmp=Path(self.temp.name)

    def run_cli(self,*args,cwd=None):
        return subprocess.run([str(ROOT/'bin/wvf'),*map(str,args)],cwd=cwd or self.tmp,capture_output=True,text=True)

    def new_project(self):
        p=self.tmp/'project'
        result=self.run_cli('new','project','--path',p)
        self.assertEqual(result.returncode,0,result.stderr)
        return p

    def test_render_options_reach_worker(self):
        cli=load_cli()
        with patch.object(sys,'argv',['wvf','render','--workers','1','--fps','30','--test']),patch.object(cli,'cmd_exec_tool',return_value=0) as call:
            with self.assertRaises(SystemExit): cli.main()
        call.assert_called_once_with('render.py',['--workers','1','--fps','30','--test'])

    def test_new_from_research_creates_complete_scaffold(self):
        src=self.tmp/'source';src.mkdir();(src/'note.txt').write_text('- Candidate fact\n')
        p=self.tmp/'project'
        result=self.run_cli('new','project','--path',p,'--from',src,'--client','Acme')
        self.assertEqual(result.returncode,0,result.stderr)
        for name in ('engine.js','index.html','inputs/research/note.txt','inputs/media','facts_candidates.md'):
            self.assertTrue((p/name).exists(),name)
        self.assertEqual(json.loads((p/'project_config.json').read_text())['client_name'],'Acme')

    def test_new_project_can_start_actual_preview_server(self):
        project = self.new_project()
        with socket.socket() as port_socket:
            port_socket.bind(('127.0.0.1', 0))
            port = port_socket.getsockname()[1]
        process = subprocess.Popen([str(ROOT/'bin/wvf'), 'start', '--no-open', '--port', str(port)], cwd=project, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail(process.stderr.read())
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/engine.js', timeout=0.3) as response:
                        self.assertIn(b'function renderAt', response.read())
                    break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail('The preview server did not start')
        finally:
            process.terminate(); process.wait(timeout=5); process.stderr.close()

    def test_init_preserves_configuration_and_custom_tools(self):
        p=self.new_project();(p/'engine.js').unlink()
        cfg={'client_name':'Acme','flow':{'project_url':'https://example.com/client'},'custom':'KEEP'}
        (p/'project_config.json').write_text(json.dumps(cfg));(p/'tools/custom.py').write_text('KEEP')
        (p/'tools/render.py').write_text('# customized renderer')
        result=self.run_cli('init',cwd=p)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads((p/'project_config.json').read_text()),cfg)
        self.assertEqual((p/'tools/custom.py').read_text(),'KEEP')
        self.assertEqual((p/'tools/render.py').read_text(),'# customized renderer')
        self.assertTrue((p/'engine.js').is_file())

    def test_init_explicit_client_update_keeps_other_fields(self):
        p=self.new_project();cfg=json.loads((p/'project_config.json').read_text());cfg['custom']='KEEP'
        (p/'project_config.json').write_text(json.dumps(cfg))
        self.assertEqual(self.run_cli('init','--client','New',cwd=p).returncode,0)
        actual=json.loads((p/'project_config.json').read_text())
        self.assertEqual(actual['client_name'],'New');self.assertEqual(actual['custom'],'KEEP')

    def test_media_ingest_preserves_verified_facts(self):
        p=self.new_project();(p/'facts.md').write_text('Verified by human\n')
        (p/'inputs/research/note.md').write_text('- Unverified source claim\n')
        result=self.run_cli('ingest',cwd=p)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((p/'facts.md').read_text(),'Verified by human\n')
        self.assertIn('Unverified source claim',(p/'facts_candidates.md').read_text())
        self.assertIn('pendientes de verificación',(p/'facts_candidates.md').read_text())

    def test_installed_tool_fallback_uses_project_directory(self):
        p=self.new_project();shutil.rmtree(p/'tools')
        self.assertEqual(self.run_cli('ingest',cwd=p).returncode,0)
        self.assertTrue((p/'facts_candidates.md').is_file())

    def valid_metadata(self):
        return {'streams':[{'codec_type':'video','width':1080,'height':1920,'r_frame_rate':'60/1','avg_frame_rate':'60/1','codec_name':'h264','pix_fmt':'yuv420p'}, {'codec_type':'audio','sample_rate':'48000','channels':2}], 'format':{'duration':'3'}}

    def test_qa_accepts_valid_technical_measurements(self):
        self.assertEqual(qa.audit_metadata(self.valid_metadata(),{'input_i':'-14','input_tp':'-1.2'}),[])

    def test_qa_rejects_each_technical_violation(self):
        for key,value in [('width',320),('height',240),('r_frame_rate','24/1'),('avg_frame_rate','30/1'),('codec_name','hevc'),('pix_fmt','yuv444p')]:
            with self.subTest(key=key):
                meta=self.valid_metadata();meta['streams'][0][key]=value
                self.assertTrue(qa.audit_metadata(meta,{'input_i':'-14','input_tp':'-1.2'}))
        for rate,channels in [('44100',2),('48000',1)]:
            meta=self.valid_metadata();meta['streams'][1].update(sample_rate=rate,channels=channels)
            self.assertTrue(qa.audit_metadata(meta,{'input_i':'-14','input_tp':'-1.2'}))
        for loud in ({},{'input_i':'-16','input_tp':'-1.2'},{'input_i':'-14','input_tp':'-0.9'},{'input_i':'-inf','input_tp':'-1.2'}):
            self.assertTrue(qa.audit_metadata(self.valid_metadata(),loud))

    def test_word_audit_detects_omissions_and_substitutions(self):
        self.assertEqual(qa.word_error_rate('Hola, envío rápido.','hola envio rapido'),0)
        self.assertAlmostEqual(qa.word_error_rate('Hola envío rápido','hola lento'),2/3)

    def test_vocal_audit_unavailable_is_a_failure(self):
        p=self.new_project();video=p/'master.mp4';video.write_bytes(b'test')
        fake=types.ModuleType('faster_whisper');fake.WhisperModel=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('unavailable'))
        result=types.SimpleNamespace(stdout=json.dumps(self.valid_metadata()))
        with patch.dict(os.environ,{'WVF_PROJECT_ROOT':str(p)}),patch.dict(sys.modules,{'faster_whisper':fake}),patch.object(qa.subprocess,'run',return_value=result),patch.object(qa,'measure_loudness',return_value={'input_i':'-14','input_tp':'-1.2'}),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(qa.main([str(video)]),1)
        self.assertIn('Auditoría vocal incompleta',(p/'check/qa_report.json').read_text())

    def test_master_name_comes_from_project_folder(self):
        self.assertEqual(env_config.project_slug('/x/SCALA OS Broma Ad'),'scala_os_broma_ad')
        self.assertEqual(env_config.project_slug('/x/Añoranza  Ágil-2'),'anoranza_agil_2')
        self.assertEqual(env_config.project_slug('/x/¡¡!!'),'video')
        self.assertEqual(env_config.get_master_path('/x/Mi Proyecto'),'/x/Mi Proyecto/mi_proyecto_master.mp4')

    def test_find_master_prefers_project_name_and_rejects_ambiguity(self):
        p=self.tmp/'Mi Proyecto';p.mkdir()
        (p/'whatsapp_ahorro_master.mp4').write_bytes(b'old')
        self.assertEqual(env_config.find_master(str(p)),str(p/'whatsapp_ahorro_master.mp4'))
        (p/'mi_proyecto_master.mp4').write_bytes(b'new')
        self.assertEqual(env_config.find_master(str(p)),str(p/'mi_proyecto_master.mp4'))
        (p/'mi_proyecto_master.mp4').unlink();(p/'otro_master.mp4').write_bytes(b'other')
        with self.assertRaisesRegex(RuntimeError,'varios masters'): env_config.find_master(str(p))

    def run_qa_outside_project(self,video,argv,loudness):
        result=types.SimpleNamespace(stdout=json.dumps(self.valid_metadata()))
        cwd=os.getcwd();os.chdir(self.tmp);self.addCleanup(os.chdir,cwd)
        with patch.dict(os.environ),patch.object(qa.subprocess,'run',return_value=result),patch.object(qa,'measure_loudness',return_value=loudness),contextlib.redirect_stdout(io.StringIO()):
            os.environ.pop('WVF_PROJECT_ROOT',None)
            return qa.main([str(video),*argv])

    def test_qa_report_goes_to_project_of_audited_file(self):
        p=self.new_project();video=p/'share/mobile_share.mp4';video.write_bytes(b'test')
        self.assertEqual(self.run_qa_outside_project(video,['--technical-only'],{'input_i':'-14','input_tp':'-1.2'}),0)
        self.assertTrue((p/'check/qa_report.json').is_file());self.assertFalse((self.tmp/'check').exists())

    def test_vocal_audit_runs_even_after_technical_failure(self):
        p=self.new_project();video=p/'project_master.mp4';video.write_bytes(b'test')
        calls=[]
        class Model:
            def __init__(self,*a,**k): pass
            def transcribe(self,path,**k):
                calls.append(path);return [types.SimpleNamespace(text='texto')],None
        fake=types.ModuleType('faster_whisper');fake.WhisperModel=Model
        with patch.dict(sys.modules,{'faster_whisper':fake}):
            self.assertEqual(self.run_qa_outside_project(video,[],{'input_i':'-20','input_tp':'-1.2'}),1)
        report=json.loads((p/'check/qa_report.json').read_text())
        self.assertEqual(len(calls),1);self.assertIn('word_error_rate',report)
        self.assertTrue(any('Volumen integrado' in e for e in report['errors']))

    def fake_ffmpeg(self,cmd,**kwargs):
        if 'ffprobe' in os.path.basename(cmd[0]):
            meta={'streams':[{'codec_type':'video'},{'codec_type':'audio'}],'format':{'duration':'10'}}
            return types.SimpleNamespace(stdout=json.dumps(meta))
        if cmd[-1].endswith('.mp4'): Path(cmd[-1]).write_bytes(b'mobile')
        return types.SimpleNamespace(stdout='')

    def test_share_limits_true_peak_and_measures_again(self):
        master=self.tmp/'p_master.mp4';master.write_bytes(b'master');out=self.tmp/'share/mobile.mp4'
        with patch.object(share.subprocess,'run',side_effect=self.fake_ffmpeg) as run,patch.object(share,'loudness',side_effect=[(-14.5,0.2),(-14.7,-1.9)]),contextlib.redirect_stdout(io.StringIO()):
            share.compress(master,out)
        limiter=run.call_args_list[-1].args[0]
        self.assertIn(share.LIMITER,limiter);self.assertEqual(limiter[limiter.index('-ar')+1],'48000')
        self.assertTrue(out.is_file())

    def test_share_does_not_send_when_limited_audio_is_out_of_spec(self):
        master=self.tmp/'p_master.mp4';master.write_bytes(b'master');out=self.tmp/'share/mobile.mp4'
        for after in ((-14.5,-0.5),(-16.2,-2.5)):
            with self.subTest(after=after):
                with patch.object(share.subprocess,'run',side_effect=self.fake_ffmpeg),patch.object(share,'loudness',side_effect=[(-14.5,0.2),after]),patch.object(wajs,'send_file') as send,contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(share.main(['--master',str(master),'--out',str(out),'--send-wa']),1)
                send.assert_not_called();self.assertFalse(out.exists())

    def test_whisper_pyav_compat_retries_only_without_metadata_errors(self):
        calls=[]
        def old_pyav_open(path, mode='r', **kwargs):
            calls.append((path, mode, dict(kwargs)))
            if 'metadata_errors' in kwargs:
                raise TypeError("open() got an unexpected keyword argument 'metadata_errors'")
            return 'container'
        wrapped=whisper_compat.compatible_open(old_pyav_open)
        self.assertEqual(wrapped('audio.wav',metadata_errors='ignore'),'container')
        self.assertEqual(calls,[('audio.wav','r',{'metadata_errors':'ignore'}),('audio.wav','r',{})])
        self.assertIs(whisper_compat.compatible_open(wrapped),wrapped)

        def unrelated_type_error(path, **kwargs):
            raise TypeError('decoder configuration invalid')
        with self.assertRaisesRegex(TypeError,'decoder configuration invalid'):
            whisper_compat.compatible_open(unrelated_type_error)('audio.wav',metadata_errors='ignore')

    def test_fix_word_preserves_length_timestamps_and_unaffected_audio(self):
        sr=48000;t=np.arange(sr)/sr
        original=(np.sin(2*np.pi*220*t)*0.2).astype('float32');patch_audio=(np.sin(2*np.pi*440*t)*0.2).astype('float32')
        words=[{'w':'la','t':0.05,'e':0.15},{'w':'API','t':0.2,'e':0.5},{'w':'funciona','t':0.6,'e':0.9}]
        patch_words=[{'w':'ápi','t':0.1,'e':0.45}]
        output,updated=fix_word.apply_patch(original,words,1,patch_audio,patch_words,0)
        self.assertEqual(len(output),len(original));np.testing.assert_array_equal(output[:9600],original[:9600]);np.testing.assert_array_equal(output[24000:],original[24000:])
        self.assertFalse(np.array_equal(output[10000:23000],original[10000:23000]))
        self.assertEqual(updated[1],{'w':'ápi','t':0.2,'e':0.5});self.assertEqual(words[1]['w'],'API')

    def test_fix_word_requires_unambiguous_existing_occurrence(self):
        words=[{'w':'API'},{'w':'ápi'}]
        self.assertEqual(fix_word.find_word(words,'API',2),1)
        with self.assertRaises(ValueError):fix_word.find_word(words,'API',3)

    def test_whatsapp_refuses_wrong_contact_before_attachment(self):
        with patch.object(wajs,'run_js',return_value='["Another contact"]') as bridge:
            with self.assertRaises(RuntimeError): wajs.send_file(self.tmp/'missing.mp4','William Romero')
        self.assertEqual(bridge.call_count,1)

    def test_whatsapp_attaches_and_clicks_preview_send(self):
        video=self.tmp/'video.mp4';video.write_bytes(b'fake test video')
        with patch.object(wajs,'run_js',side_effect=['["William Romero"]','ok','ATTACHED','SENT']) as bridge:
            wajs.send_file(video,'William Romero')
        self.assertEqual(bridge.call_count,4)

    def test_whatsapp_refuses_contact_changed_during_upload(self):
        video = self.tmp/'video.mp4'; video.write_bytes(b'fake test video')
        with patch.object(wajs, 'run_js', side_effect=['["William Romero"]', 'ok', 'ATTACHED', 'WRONG_CONTACT']):
            with self.assertRaisesRegex(RuntimeError, 'cambió'):
                wajs.send_file(video, 'William Romero')

    def test_installer_preserves_custom_skill(self):
        custom=self.tmp/'skills/webres-video-factory';custom.mkdir(parents=True);(custom/'SKILL.md').write_text('CUSTOM')
        # Execute the real registration block without dependency downloads or global changes.
        source=(ROOT/'install.sh').read_text();block=source[source.index('for skill_path in'):source.index('\necho "✓ 7 Skills')]
        env=dict(os.environ,DIR=str(ROOT),GLOBAL_SKILLS_DIR=str(self.tmp/'skills'),USER_AGENTS_DIR=str(self.tmp/'agents'))
        (self.tmp/'agents').mkdir()
        result=subprocess.run(['bash','-c',block],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual((custom/'SKILL.md').read_text(),'CUSTOM')
        self.assertTrue((self.tmp/'agents/webres-video-factory').is_symlink())
        self.assertEqual(subprocess.run(['bash','-c',block],env=env,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
