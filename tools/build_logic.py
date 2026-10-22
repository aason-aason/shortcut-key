"""Apple 公式の Logic Pro ユーザガイド「キーコマンドの表」から data/logic-pro.js を作る。

使い方: python3 tools/build_logic.py <キャッシュ用フォルダ>
  日本語版（機能名・JIS配列のキー）と英語版（US配列のキー・テンキーの印）を行ごとに突き合わせる。
  ガイドのHTMLはキャッシュ用フォルダに保存し、リポジトリには入れない。
  言いかえ語・覚え方は tools/logic_extra.py に手で書いたものを足す。
"""
import html, json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from logic_extra import BASIC, EXTRA  # noqa: E402

BASE = 'https://support.apple.com/{lang}/guide/logicpro/{pid}/mac'

# ガイドのページ → (画面の短い名前, 画面のまとまり)
PAGES = [
    ('lgcp02bf31b6', 'どこでも', 'any'),
    ('lgcp3bc760d6', 'コントロールサーフェス', 'any'),
    ('lgcp665bbccc', 'いろいろな画面', 'any'),
    ('lgcp7afa650a', 'オーディオ表示', 'main'),
    ('lgcpe8314fe2', 'トラック・エディタ', 'main'),
    ('lgcp205eef3d', 'エディタ共通', 'main'),
    ('lgcp267f63a1', 'タイムルーラ', 'main'),
    ('lgcp771facc4', 'オートメーション', 'main'),
    ('lgcpb99be9c5', 'トラック', 'main'),
    ('lgcp221018cf', 'Live Loops', 'live'),
    ('lgcp2dc3f212', 'ミキサー', 'mixer'),
    ('lgcpbaed502c', 'MIDIエンバイロメント', 'env'),
    ('lgcpfa34642b', 'ピアノロール', 'piano'),
    ('lgcpe96f8c91', 'スコアエディタ', 'score'),
    ('lgcp359efbac', 'イベントリスト', 'event'),
    ('lgcp07d08878', 'ステップエディタ', 'stepedit'),
    ('lgcp1d6a34a9', 'ステップシーケンサー', 'stepseq'),
    ('lgcp338f38f7', 'プロジェクトオーディオ', 'audio'),
    ('lgcpfd2cc3d1', 'オーディオファイルエディタ', 'audio'),
    ('lgcp9ee9193b', 'スマートテンポエディタ', 'audio'),
    ('lgcpa6a41488', 'ライブラリ', 'sound'),
    ('lgcp8142940c', 'Sampler', 'sound'),
    ('lgcp1a968d53', 'Drum Machine Designer', 'sound'),
    ('lgcp4fe41fb3', 'ステップ入力キーボード', 'stepin'),
    ('lgcp7e241e00', 'Smart Control', 'sound'),
    ('lgcp0182c4e5', 'ツールメニュー', 'tool'),
]
GROUPS = [
    ('any', 'どこでも'), ('main', 'メイン画面'), ('mixer', 'ミキサー'), ('piano', 'ピアノロール'),
    ('score', 'スコアエディタ'), ('event', 'イベントリスト'), ('stepedit', 'ステップエディタ'),
    ('stepseq', 'ステップシーケンサー'), ('stepin', 'ステップ入力キーボード'), ('audio', 'オーディオ編集'),
    ('live', 'Live Loops'), ('sound', '音源・ライブラリ'), ('env', 'MIDIエンバイロメント'), ('tool', 'ツールメニュー'),
]

# 場面の振り分け（上から順に最初に当てはまったもの）。言いかえ語の段階で手で見直す
SCENE_RULES = [
    ('file', r'保存|新規プロジェクト|テンプレートから|^開く$|書き出|読み込|プリント|^終了$|プロジェクト設定|プロジェクトを閉じる|^バウンス$'),
    ('rec', r'録音|カウントイン|パンチ|テイク|コンプ|メトロノーム|入力モニタ|Flashback'),
    ('range', r'マーカー|ロケータ|サイクル'),
    ('track', r'新規.*トラック|トラックを(削除|検索)|使用されていないトラック|Track Stack|スタックを|スタックを作成|代替トラック|トラック名|トラックのオン|トラックヘッダ'),
    ('select', r'を選択|すべてを選択|選択を解除|選択項目を反転|選択を(上|下)へ拡張'),
    ('mix', r'ミュート|ソロ|ミキサー|オートメーション|チャンネルストリップ|プラグイン|グループ|パン|ボリューム|ゲイン|センド|バス'),
    ('view', r'表示|ズーム|拡大|縮小|スクロール|ウインドウ|スクリーンセット|フルスクリーン|を開く|ヘルプ|しまう'),
    ('play', r'再生|停止|早戻し|早送り|一時停止|先頭に移動|位置の移動|プレビュー|キャッチ|スクロールプレイ|最後に移動|末尾に移動'),
    ('midi', r'ノート|MIDI|ミュージックタイピング|ベロシティ|コード|ステップ'),
]
PAGE_SCENE = {'tool': 'tool', 'mixer': 'mix', 'piano': 'midi', 'score': 'score', 'event': 'midi',
              'stepedit': 'midi', 'stepseq': 'midi', 'stepin': 'midi', 'env': 'midi', 'audio': 'audio',
              'live': 'live', 'sound': 'sound'}

MODS_JP = {'Control': 'ctrl', 'Option': 'opt', 'Shift': 'shift', 'Shif': 'shift', 'Xhift': 'shift', 'Command': 'cmd'}
MODS_EN = {'Control': 'ctrl', 'Option': 'opt', 'Shift': 'shift', 'Command': 'cmd'}
KEY_JP = {
    '左矢印（←）': '←', '右矢印（→）': '→', '上矢印（↑）': '↑', '下矢印（↓）': '↓', 'Delete（⌫）': 'Delete',
    'Return（↩）': 'Return', 'Return（↩︎）': 'Return', 'ピリオド（.）': '.', 'カンマ（,）': ',', '等号（=）': '=',
    '右角かっこ（]）': ']', '左角かっこ（[）': '[', 'ハイフン（-）': '-', 'ハイフン（–）': '-', 'スペースバー': 'Space',
    'スラッシュ（/）': '/', 'アポストロフィ（’）': "'", 'Home（↖）': 'Home', 'End（↘）': 'End', 'キャレット（^）': '^',
    '\\': '\\', '￥': '¥', 'セミコロン（;）': ';', 'Enter（⌅）': 'Enter', '⌅': 'Enter', 'アンダーバー（_）': '_',
    'Tab（⇥）': 'Tab', '⇞': 'PgUp', '⇟': 'PgDn', '上にスクロール（⇞）キー': 'PgUp', '下にスクロール（⇟）キー': 'PgDn',
    '上にスクロール（⇞）': 'PgUp', '下にスクロール（⇟）': 'PgDn', 'アスタリスク（*）': '*', 'Forward delete（⌦）': 'FwdDel',
    'Forward Delete（⌦）': 'FwdDel', '低アクセント記号（`）': '`', 'バックスラッシュ（\\）': '\\',
}
KEY_EN = {
    'Left Arrow (←)': '←', 'Right Arrow (→)': '→', 'Up Arrow (↑)': '↑', 'Down Arrow (↓)': '↓', 'Delete (⌫)': 'Delete',
    'Return (↩)': 'Return', 'Return (↩︎)': 'Return', 'Period (.)': '.', 'Comma (,)': ',', 'Equal Sign (=)': '=',
    'Right Bracket (])': ']', 'Left Bracket ([)': '[', 'Hyphen (-)': '-', 'Hyphen (–)': '-', 'Space bar': 'Space',
    'Slash (/)': '/', 'Apostrophe (’)': "'", 'Home (↖)': 'Home', 'End (↘)': 'End', 'Backslash (\\)': '\\',
    'Semicolon (;)': ';', 'Enter (⌅)': 'Enter', 'Tab (⇥)': 'Tab', 'Page Up (⇞)': 'PgUp', 'Page Down (⇟)': 'PgDn',
    'Asterisk (*)': '*', 'Forward delete (⌦)': 'FwdDel', 'Forward Delete (⌦)': 'FwdDel', 'Grave Accent (`)': '`',
}
NOTE_RE = re.compile(r'[（(]\s*(?:「コードを編集」ダイアログが開いているとき|when Edit Chord dialog is open)\s*[）)]')


def fetch(cache, lang, pid):
    path = os.path.join(cache, f'{lang}-{pid}.html')
    if not os.path.exists(path):
        with urllib.request.urlopen(BASE.format(lang=lang, pid=pid)) as r, open(path, 'wb') as f:
            f.write(r.read())
    return open(path, encoding='utf8').read()


def text(x):
    return html.unescape(re.sub(r'<[^>]+>', '', x)).strip()


def table_rows(page):
    out = []
    for tr in re.findall(r'<tr>(.*?)</tr>', page, re.S):
        td = [text(x) for x in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if td:
            out.append(td)
    return out


def parse_jp(k):
    note = bool(NOTE_RE.search(k))
    k = NOTE_RE.sub('', k).strip()
    k = re.sub(r'\s*\$1\$2$', '', k)  # ガイド側の文字化け。キーは英語版から補う
    parts = [p.strip() for p in re.split(r'\s*[＋+]\s*', k) if p.strip()]
    mods = [MODS_JP[p] for p in parts if p in MODS_JP]
    rest = [p for p in parts if p not in MODS_JP]
    key = KEY_JP.get(rest[0], rest[0]) if rest else None
    return mods, key, note


def parse_en(k):
    pad = k.startswith('𝍖')
    k = NOTE_RE.sub('', k.lstrip('𝍖').strip()).strip()
    mods = []
    while True:
        m = re.match(r'(Control|Option|Shift|Command)-', k)
        if not m:
            break
        mods.append(MODS_EN[m.group(1)])
        k = k[m.end():]
    return mods, KEY_EN.get(k, k), pad


def scene_of(name, group):
    if group == 'tool':
        return 'tool'
    for sc, pat in SCENE_RULES:
        if re.search(pat, name):
            return sc
    return PAGE_SCENE.get(group, 'edit')


def main(cache):
    os.makedirs(cache, exist_ok=True)
    items, warn, n = [], [], 0
    for pid, win, group in PAGES:
        jp, en = table_rows(fetch(cache, 'ja-jp', pid)), table_rows(fetch(cache, 'en-us', pid))
        if len(jp) != len(en):
            sys.exit(f'{pid}: 日本語版と英語版で行数が違う ({len(jp)} / {len(en)})')
        for (name, kjp), (_, ken) in zip(jp, en):
            n += 1
            if not ken.strip() and not kjp.strip():
                continue  # 初期設定でキーの割り当てがない
            emods, ekey, pad = parse_en(ken)
            jmods, jkey, note = parse_jp(kjp)
            if sorted(emods) != sorted(jmods) and '$1$2' not in kjp and 'Xhift' not in kjp:
                warn.append(f'修飾キーが違う: {win} {name} / {kjp} / {ken}')
            it = {'id': f'l{n}', 'name': name, 'key': ekey, 'mods': [m for m in ('ctrl', 'opt', 'shift', 'cmd') if m in emods],
                  'win': win, 'g': group, 'scene': scene_of(name, group)}
            # JIS配列で位置の違う記号キーだけを jk に残す。それ以外の食い違いはガイドどうしの違いとして要確認にする
            if jkey and jkey != ekey and '$1$2' not in kjp:
                if ekey in ('`', '\\') and jkey in ('^', '¥', '_'):
                    it['jk'] = jkey
                else:
                    it['chk'] = 1
                    warn.append(f'日本語版と英語版でキーが違う（英語版を採用）: {win} {name} / {kjp} / {ken}')
            if sorted(emods) != sorted(jmods) and '$1$2' not in kjp and 'Xhift' not in kjp:
                it['chk'] = 1
            if (win, name) in BASIC:
                it['basic'] = 1
            if pad:
                it['pad'] = 1
            if note:
                it['note'] = '「コードを編集」ダイアログが開いているとき'
            ex = dict(EXTRA.get((win, name)) or {})
            # _keep: 自動で振り分けた場面がこの中なら、まとめて指定した場面より優先する
            if it['scene'] in ex.pop('_keep', ()):
                ex.pop('scene', None)
            it.update(ex)
            items.append(it)
    missing = [k for k in list(EXTRA) + list(BASIC) if not any((i['win'], i['name']) == k for i in items)]
    for k in missing:
        warn.append(f'言いかえ語の行き先が見つからない: {k}')
    out = os.path.join(os.path.dirname(__file__), '..', 'data', 'logic-pro.js')
    with open(out, 'w', encoding='utf8') as f:
        f.write('// Logic Pro のショートカット。tools/build_logic.py が Apple 公式ユーザガイド「キーコマンドの表」から作る（手で直さない）\n')
        f.write('// 項目: name 機能名 / key US配列のキー / jk JIS配列で違うときのキー / mods 修飾キー / pad テンキー /\n')
        f.write('//       win 使う画面 / g 画面のまとまり / scene 場面 / basic 「基本」にも出す / mn 覚え方 / tags 言いかえ語 /\n')
        f.write('//       note 注意 / chk 日本語版と英語版のガイドで食い違いがあり要確認（英語版のキーを採用）\n')
        f.write('(window.KK_APPS=window.KK_APPS||[]).push({id:\'logic\',name:\'Logic Pro\',version:\'12\',platform:\'mac\',\n')
        f.write(' source:\'Apple「Mac用Logic Proユーザガイド」キーコマンドの表\',\n')
        f.write(' groups:' + json.dumps([{'id': g, 'name': nm} for g, nm in GROUPS], ensure_ascii=False) + ',\n')
        f.write(' items:[\n')
        f.write(',\n'.join(' ' + json.dumps(i, ensure_ascii=False, separators=(',', ':')) for i in items))
        f.write('\n]});\n')
    print(f'{len(items)}件を書き出し（表の行は{n}行）')
    for w in warn:
        print('注意:', w)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.cache/apple')
