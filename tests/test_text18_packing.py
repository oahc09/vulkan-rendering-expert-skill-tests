import pytest
from text_atlas_packing import ShelfAtlas


def rect(w,h,v=.5):return w,h,[v]*(w*h)

@pytest.mark.host_unit
def test_grows_pages_without_relocation_or_padding_bleed():
    atlas=ShelfAtlas(8,8,max_pages=3);batch=atlas.prepare([rect(4,4,.25),rect(4,4,.75)])
    assert not atlas.pages
    locations=atlas.publish(batch);assert [p.page for p in locations]==[0,1]
    snap=atlas.snapshot()
    for loc,value in zip(locations,[.25,.75]):
        pixels=snap[loc.page]
        assert pixels[loc.y*8+loc.x]==value
        assert all(pixels[y*8+x]==0 for y in range(8) for x in range(8) if not (loc.x<=x<loc.x+4 and loc.y<=y<loc.y+4))
    atlas.publish(atlas.prepare([rect(1,1)]))
    assert atlas.snapshot()[:2]==snap

@pytest.mark.host_unit
def test_atomic_batch_budget_failure_keeps_snapshot_and_revision():
    atlas=ShelfAtlas(8,8,max_pages=1);atlas.publish(atlas.prepare([rect(4,4)]));before=atlas.snapshot();rev=atlas.revision
    with pytest.raises(ValueError):atlas.prepare([rect(4,4),rect(4,4)])
    assert atlas.snapshot()==before and atlas.revision==rev

@pytest.mark.parametrize('r',[(7,1,[1]*7),(True,1,[1]),(2,2,[1]),(1,1,[float('nan')]),(1,1,[-.1])])
@pytest.mark.host_unit
def test_invalid_rectangles_rejected_before_state(r):
    a=ShelfAtlas(8,8)
    with pytest.raises(ValueError):a.prepare([r])
    assert not a.pages and a.revision==0

@pytest.mark.host_unit
def test_sealed_page_never_accepts_new_uploads():
    a=ShelfAtlas(16,16);p=a.publish(a.prepare([rect(2,2)]))[0];snapshot=a.snapshot();a.seal(p.page)
    q=a.publish(a.prepare([rect(2,2)]))[0]
    assert q.page!=p.page and a.snapshot()[0]==snapshot[0]

@pytest.mark.host_unit
def test_cancelled_and_competing_batches_cannot_publish():
    a=ShelfAtlas();b=a.prepare([rect(2,2)]);a.cancel(b)
    with pytest.raises(ValueError):a.publish(b)
    b=a.prepare([rect(2,2)]);c=a.prepare([rect(2,2)])
    a.publish(b)
    with pytest.raises(ValueError):a.publish(c)
    with pytest.raises(ValueError):a.publish(b)

@pytest.mark.host_unit
def test_snapshot_and_staging_do_not_alias_published_pixels():
    a=ShelfAtlas();b=a.prepare([rect(2,2)]);a.publish(b);snap=a.snapshot()
    b.pages[0]['pixels'][0]=1
    assert a.snapshot()==snap

@pytest.mark.host_unit
def test_shelf_positions_nonoverlap_with_padding():
    a=ShelfAtlas(24,24,max_pages=4)
    pos=a.publish(a.prepare([rect(w,h) for w,h in [(2,3),(3,2),(8,5),(4,6),(2,2)]]))
    for i,p in enumerate(pos):
        for q in pos[i+1:]:
            if p.page!=q.page:continue
            assert p.x+p.width+1<=q.x-1 or q.x+q.width+1<=p.x-1 or p.y+p.height+1<=q.y-1 or q.y+q.height+1<=p.y-1


@pytest.mark.host_unit
def test_foreign_atlas_candidate_is_rejected():
    a=ShelfAtlas();b=ShelfAtlas();candidate=a.prepare([rect(2,2)])
    with pytest.raises(ValueError):b.publish(candidate)
    assert not b.pages


@pytest.mark.vulkan_integration
def test_actual_packed_font_pages(tmp_path):
    import os,sys,json,subprocess
    from pathlib import Path
    if os.environ.get('VULKAN_TEXT18_BITMAP')!='1':pytest.skip('actual Vulkan plus trusted font opt-in')
    lab=Path(__file__).parent/'fixtures/text_bitmap_lab/run_lab.py';out=tmp_path/'packed'
    subprocess.run([sys.executable,str(lab),'--packing','--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--out',str(out)],check=True,timeout=240)
    p=json.loads((out/'summary.json').read_text())['packing']
    assert p['final_pages']>p['initial_pages'] and all(r['validation_enabled'] for r in p['cases'])
