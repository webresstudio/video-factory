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
import chromejs
import social_analytics
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
        (p/'tools').mkdir();(p/'project_config.json').write_text(json.dumps(cfg));(p/'tools/custom.py').write_text('KEEP')
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

    def test_new_project_keeps_no_tool_copies_and_uses_package(self):
        p=self.new_project()
        self.assertFalse(any((p/'tools').glob('*')) if (p/'tools').exists() else False)
        self.assertEqual(self.run_cli('ingest',cwd=p).returncode,0)
        self.assertTrue((p/'facts_candidates.md').is_file())

    def test_init_force_never_touches_project_tools(self):
        p=self.new_project();(p/'tools').mkdir()
        (p/'tools/render.py').write_text('# customized renderer');(p/'tools/qa.py').write_text('# legacy copy')
        self.assertEqual(self.run_cli('init','--force',cwd=p).returncode,0)
        self.assertEqual((p/'tools/render.py').read_text(),'# customized renderer')
        self.assertEqual((p/'tools/qa.py').read_text(),'# legacy copy')
        self.assertEqual(sorted(f.name for f in (p/'tools').iterdir()),['qa.py','render.py'])

    def test_tool_resolution_prefers_project_copy(self):
        p=self.tmp/'p';(p/'tools').mkdir(parents=True);(p/'tools/build_timeline.py').write_text('# own')
        self.assertEqual(env_config.tool_command('build_timeline.py',root=str(p))[1],str(p/'tools/build_timeline.py'))
        self.assertEqual(env_config.tool_command('render.py',root=str(p))[1],str(ROOT/'kit/tools/render.py'))
        self.assertEqual(env_config.tool_command('download_all.sh',root=str(p))[0],'bash')

    def test_project_tool_imports_package_modules_through_wvf(self):
        p=self.new_project();(p/'tools').mkdir()
        (p/'tools/own_tool.py').write_text('import sys, env_config\nopen("marker","w").write(env_config.kit_tools_dir()+"|"+" ".join(sys.argv[1:]))\n')
        result=self.run_cli('tool','own_tool','--flag','L01',cwd=p)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((p/'marker').read_text(),str(ROOT/'kit/tools')+'|--flag L01')

    def test_project_module_overrides_package_module_for_package_tools(self):
        kit=self.tmp/'kit';kit.mkdir();p=self.tmp/'p';(p/'tools').mkdir(parents=True)
        (kit/'runner.py').write_text('import shared\nprint(shared.WHO)\n');(kit/'shared.py').write_text('WHO="kit"\n')
        (p/'tools/shared.py').write_text('WHO="project"\n')
        with patch.dict(os.environ,{'WVF_KIT_TOOLS':str(kit)}):
            out=subprocess.run(env_config.tool_command('runner.py',root=str(p)),env=env_config.tool_env(str(p)),capture_output=True,text=True)
        self.assertEqual(out.stdout.strip(),'project',out.stderr)

    def test_tool_command_finds_shell_tools_without_extension(self):
        cli=load_cli()
        with patch.object(sys,'argv',['wvf','tool','download_all']),patch.object(cli,'cmd_exec_tool',return_value=0) as call:
            with self.assertRaises(SystemExit): cli.main()
        call.assert_called_once_with('download_all.sh',[])

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
        source=(ROOT/'install.sh').read_text();block=source[source.index('for skill_path in'):source.index('\necho "✓ 15 Skills')]
        env=dict(os.environ,DIR=str(ROOT),GLOBAL_SKILLS_DIR=str(self.tmp/'skills'),USER_AGENTS_DIR=str(self.tmp/'agents'),CLAUDE_SKILLS_DIR=str(self.tmp/'claude'))
        (self.tmp/'agents').mkdir();(self.tmp/'claude').mkdir()
        result=subprocess.run(['bash','-c',block],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual((custom/'SKILL.md').read_text(),'CUSTOM')
        self.assertTrue((self.tmp/'agents/webres-video-factory').is_symlink())
        self.assertTrue((self.tmp/'claude/webres-video-factory').is_symlink())
        self.assertTrue((self.tmp/'agents/hyperframes-causal-cursor').is_symlink())
        self.assertTrue((self.tmp/'agents/social-analytics-audit').is_symlink())
        self.assertEqual(subprocess.run(['bash','-c',block],env=env,capture_output=True).returncode,0)

    def test_audit_script_subcommand_runs(self):
        sample=ROOT/'skills/viral-listicle-story/scripts/audit_listicle.py'
        self.assertTrue(sample.is_file())
        draft=self.tmp/'draft.json'
        draft.write_text(json.dumps({
            'takes': [
                {'id': 'L01', 'cuts_sec': [1.8, 3.2], 'screen_text': 'CREA APPS SIN CÓDIGO', 'spoken': 'Suelta Claude Code un minuto. Sé que le haces el feo a Antigravity, pero es mejor.'},
                {'id': 'L02', 'cuts_sec': [2.8, 2.4], 'screen_text': 'OTROS CHATS FALLAN', 'spoken': 'Puro desastre. Sin ser experto, pides una página en cualquier otro chat y te arruina toda la tarde.'},
                {'id': 'L03', 'cuts_sec': [1.2, 3.5], 'screen_text': '1 · /grill-me', 'spoken': 'Aquí no. Pones grill-me y te entrevista antes con respuestas sugeridas.'},
                {'id': 'L04', 'cuts_sec': [2.5, 2.5], 'screen_text': 'LOS COMANDOS', 'spoken': 'Mándaselo a tu amigo sin código o al que sigue casado con Claude Code.'},
            ]
        }))
        res=self.run_cli('audit-script',draft,'--lang','es')
        self.assertEqual(res.returncode,0,res.stdout+res.stderr)
        guion_md=self.tmp/'GUION.md'
        guion_md.write_text('\n'.join([
            '| Toma | Cortes | Texto | Acción | Voz | Pal |',
            '|---|---|---|---|---|---|',
            '| L01 | PC (0–1.8s) → PD (1.8–5.0s) | BUILD APPS FAST | A/B | Quit worshipping Claude Code for forty-five seconds. Antigravity has six commands way better. | 13 |',
            '| L02 | GRAF (5.0–7.8s) → PV (7.8–10.2s) | OTHER CHATS FAIL | Stake | Pure mess. Normal AI chats guess wrong and wreck your whole afternoon. | 12 |',
            '| L03 | PC (10.2–11.4s) → PD (11.4–14.9s) | 1 · /grill-me | Interview | Not here. Type grill-me first, and it interviews you with suggested answers. | 12 |',
            '| L04 | GRAF (14.9–17.4s) → PD (17.4–19.9s) | SAVE THIS MAP | Save + DM | Send this to your friend with zero code, or the one married to Claude Code. | 15 |',
        ]))
        res_md=self.run_cli('audit-script',guion_md,'--lang','en')
        self.assertEqual(res_md.returncode,0,res_md.stdout+res_md.stderr)

    def test_chromejs_lists_navigates_and_opens_missing_tab_when_requested(self):
        sample_tabs = "1\t1\thttps://www.tiktok.com/tiktokstudio/analytics\tTikTok Studio\n1\t2\thttps://www.instagram.com/webresstudio/\tInstagram\n"
        with patch.object(chromejs, 'run_applescript', return_value=sample_tabs):
            filtered = chromejs.list_tabs('tiktok')
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]['title'], 'TikTok Studio')

        with patch.object(chromejs, 'run_applescript', side_effect=['NO_MATCHING_TAB', 'NAVIGATED_EXISTING', 'READY_DOM']) as mock_osa:
            output = chromejs.execute_javascript(
                'document.title',
                url_match='business.facebook.com',
                open_if_missing_url='https://business.facebook.com/latest/insights/content',
                wait_seconds=0,
            )
            self.assertEqual(output, 'READY_DOM')
            self.assertEqual(mock_osa.call_count, 3)

        with patch.object(chromejs, 'run_applescript', return_value='NO_MATCHING_TAB'):
            with self.assertRaisesRegex(RuntimeError, 'business.facebook.com'):
                chromejs.execute_javascript('document.title', url_match='business.facebook.com')

    def test_social_analytics_parses_tiktok_meta_and_instagram_studios(self):
        tiktok_summary = "\n".join([
            "6 comandos de Google Antigravity",
            "Publicado el 29/10/2026",
            "9,457", "1,721", "0", "4", "61",
            "Vistas del video", "9.5K",
            "Tiempo promedio de vista", "3.16s",
            "Vieron el video completo", "0.3%",
            "Nuevos seguidores", "11",
            "La mayoría de los espectadores dejaron de mirar el video en el minuto 0:02.",
            "Para ti", "99.5%",
            "Buscar", "<0.1%",
        ])
        tiktok_audience = "\n".join([
            "Edad", "18-24", "48%", "25-34", "33%", "35-44", "10%",
            "Ubicaciones", "Guatemala", "99.5%",
        ])
        parsed_tt = social_analytics.parse_tiktok_video_analytics("7702088675", tiktok_summary, tiktok_audience)
        self.assertEqual(parsed_tt["views"], 9500)
        self.assertEqual(parsed_tt["likes"], 1721)
        self.assertEqual(parsed_tt["saves"], 61)
        self.assertEqual(parsed_tt["average_watch_seconds"], 3.16)
        self.assertEqual(parsed_tt["watched_full_percent"], 0.3)
        self.assertEqual(parsed_tt["primary_dropoff_timestamp"], "0:02")
        self.assertEqual(parsed_tt["age_brackets"]["18-24"], 48.0)

        overview = social_analytics.parse_tiktok_account_overview(
            "Fuente de tráfico\nPara ti\n98.5%\nBuscar\n0.3%",
            "En los últimos 7 días, tus espectadores estuvieron más activos el 3 nov entre las 1pm y las 2pm.",
        )
        self.assertEqual(overview["account_search_traffic_percent"], 0.3)
        self.assertEqual(overview["peak_activity_window"], "1pm y las 2pm")

        meta_rows = [
            ["Title", "Date", "Views", "Reach", "Viewers", "Inter", "Likes", "Comm", "Shares", "Saves", "Clicks", "Rep", "Follows", "Watch", "Avg", "3s"],
            ["6 comandos Antigravity Reel webresstudio Boost", "Fri Nov 6, 7:00am", "147", "110", "--", "17", "12", "2", "0", "0", "--", "--", "0", "19m 20s", "10s", "--"],
            ["4 noticias tech Reel Crossposted Webres Studio, webresstudio", "Mon Nov 2, 8:30am", "300", "--", "199", "17", "10", "3", "0", "0", "0", "--", "0", "419,679", "2s", "15"],
            ["4 noticias tech Reel Crossposted Webres Studio, webresstudio", "Mon Nov 2, 8:30am", "300", "--", "199", "17", "10", "3", "0", "0", "0", "--", "0", "419,679", "2s", "15"],
        ]
        parsed_meta = social_analytics.parse_meta_business_suite_rows(meta_rows)
        self.assertEqual(len(parsed_meta), 2)
        self.assertFalse(parsed_meta[0]["is_crossposted"])
        self.assertEqual(parsed_meta[0]["average_play_seconds"], 10.0)
        self.assertTrue(parsed_meta[1]["is_crossposted"])
        self.assertEqual(parsed_meta[1]["average_play_seconds"], 2.0)

        parsed_ig = social_analytics.parse_instagram_reel_insights(
            "https://www.instagram.com/webresstudio/reel/DfZqfAKAWS3/",
            "Visualizaciones\nVisualizaciones\n146\nNo seguidores\n75.2%\nEspectadores\n111\nMe gusta\n12\nComentarios\n2\nVeces que se guardó\n0\nVeces que se compartió\n0\nActividad del perfil\n0",
            {"title": "6 comandos", "time": "2026-11-06", "aiLabel": True},
        )
        self.assertEqual(parsed_ig["views"], 146)
        self.assertEqual(parsed_ig["non_followers_percent"], 75.2)
        self.assertTrue(parsed_ig["has_ai_content_label"])

    def test_social_analytics_adapts_diagnosis_across_business_models(self):
        sample_tt = [{
            "video_id": "v1",
            "average_watch_seconds": 9.5,
            "watched_full_percent": 30.0,
            "primary_dropoff_timestamp": "0:08",
            "age_brackets": {"18-24": 48.0, "25-34": 30.0},
        }]
        sample_ig = [{"views": 400, "saves": 0, "shares": 0, "has_ai_content_label": False}]

        b2b_eval = social_analytics.evaluate_social_performance(
            business_model="b2b_high_ticket",
            tiktok_videos=sample_tt,
            meta_items=[],
            instagram_reels=sample_ig,
            tiktok_overview={"account_search_traffic_percent": 5.0},
        )
        b2b_codes = {f["code"] for f in b2b_eval["findings"]}
        self.assertIn("AUDIENCE_AGE_MISMATCH", b2b_codes)
        self.assertIn("ZERO_SAVES_AND_DM_SHARES", b2b_codes)
        self.assertIn("WATCH_TIME_BELOW_MODEL_TARGET", b2b_codes)
        self.assertEqual(b2b_eval["recommended_duration_seconds"], [30, 45])

        ecom_eval = social_analytics.evaluate_social_performance(
            business_model="ecommerce_b2c",
            tiktok_videos=sample_tt,
            meta_items=[],
            instagram_reels=sample_ig,
            tiktok_overview={"account_search_traffic_percent": 5.0},
        )
        ecom_codes = {f["code"] for f in ecom_eval["findings"]}
        self.assertNotIn("AUDIENCE_AGE_MISMATCH", ecom_codes)
        self.assertNotIn("ZERO_SAVES_AND_DM_SHARES", ecom_codes)
        self.assertNotIn("WATCH_TIME_BELOW_MODEL_TARGET", ecom_codes)
        self.assertEqual(ecom_eval["recommended_duration_seconds"], [12, 25])

    def test_analytics_cli_subcommand_routes_and_init_persists_social_config(self):
        project_dir = self.tmp / "avalo_client"
        res = self.run_cli(
            "new", "avalo_client",
            "--path", project_dir,
            "--client", "AVALO CORP",
            "--business-model", "b2b_high_ticket",
            "--ig-handle", "@avalocorp",
            "--meta-asset-id", "1027787490574070",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        saved_cfg = json.loads((project_dir / "project_config.json").read_text())
        self.assertEqual(saved_cfg["social"]["business_model"], "b2b_high_ticket")
        self.assertEqual(saved_cfg["social"]["instagram_handle"], "avalocorp")
        self.assertEqual(saved_cfg["social"]["meta_asset_id"], "1027787490574070")
        meta_url = social_analytics.build_meta_insights_url(
            social_analytics.load_social_configuration(str(project_dir))
        )
        self.assertIn("asset_id=1027787490574070", meta_url)

        cli = load_cli()
        with patch.object(sys, "argv", ["wvf", "analytics", "--platform", "meta", "--limit", "3", "--model", "b2b_high_ticket"]), patch.object(cli, "cmd_exec_tool", return_value=0) as mock_exec:
            with self.assertRaises(SystemExit):
                cli.main()
        mock_exec.assert_called_once_with("social_analytics.py", ["--platform", "meta", "--limit", "3", "--model", "b2b_high_ticket"])


if __name__=='__main__':unittest.main()
