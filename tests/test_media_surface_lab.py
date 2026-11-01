"""Negative/positive state fixtures, not actual API execution."""
import pytest
from media_surface_lab import Lab, ContractError, simulate


def test_100_rebuilds_1000_dual_consumer_frames():
    report = simulate()
    assert report['rebuilds'] == 100 and report['dual_consumer_frames'] == 1000
    assert report['returned'] == 1000 and report['outstanding_leases'] == 0
    assert report['peak_leases'] <= 4
    assert report['layer'] == 'Static' and not report['gpu_executed']


def test_stale_generation_and_callback_ack():
    lab = Lab()
    with pytest.raises(ContractError):
        lab.destroy_output('A', 1, False)
    lab.outputs['A'].accessing = True
    with pytest.raises(ContractError):
        lab.destroy_output('A', 1, True)
    lab.outputs['A'].accessing = False
    lab.destroy_output('A', 1, True)
    lab.recreate_output('A')
    assert not lab.destroy_output('A', 1, True)
    assert lab.outputs['B'].active
    f = lab.acquire(1)
    with pytest.raises(ContractError):
        lab.submit(f, 'A', 1)
    lab.submit(f, 'A', 2)


def test_failed_import_fd_zero_and_no_double_close():
    lab = Lab(); f = lab.acquire(1, fd=0)
    lab.import_fd(f, False)
    assert f.fd_owner == 'app'
    with pytest.raises(ContractError):
        lab.submit(f, 'A', 1)
    with pytest.raises(ContractError):
        lab.close_app_fd(f)
    lab.ready(f); lab.close_app_fd(f)
    with pytest.raises(ContractError):
        lab.close_app_fd(f)
    lab.release_ownership(f); assert lab.return_frame(f)
    with pytest.raises(ContractError):
        lab.return_frame(f)


def test_successful_import_transfers_fd_and_partial_submit_retains_lease():
    lab = Lab(); f = lab.acquire(1, fd=9)
    lab.import_fd(f, True)
    with pytest.raises(ContractError):
        lab.close_app_fd(f)
    lab.ready(f); lab.submit(f, 'A', 1)
    lab.submit(f, 'B', 1, success=False)
    assert f.consumers == {'A': 'pending'}
    with pytest.raises(ContractError):
        lab.release_ownership(f)
    lab.complete(f, 'A'); lab.release_ownership(f)
    assert not lab.return_frame(f, export_success=False)
    assert f.frame_id in lab.leases
    assert lab.return_frame(f)  # Modeled host-complete fallback, not fabricated FD.


def test_bounded_backpressure_and_source_generation():
    lab = Lab(max_images=3)
    f = lab.acquire(1)
    assert lab.latest_can_discard()
    lab.acquire(2)
    assert not lab.latest_can_discard()
    lab.acquire(3)
    with pytest.raises(ContractError):
        lab.acquire(4)
    with pytest.raises(ContractError):
        lab.change_source()
    for frame in list(lab.leases.values()):
        lab.release_ownership(frame); lab.return_frame(frame)
    lab.change_source()
    with pytest.raises(ContractError):
        lab.submit(f, 'A', 1)
    assert lab.acquire(4).generation == 2


def test_device_loss_is_not_local_surface_recovery_or_completion():
    lab = Lab(); f = lab.acquire(1)
    lab.submit(f, 'A', 1); lab.device_lost = True
    for action in [lambda: lab.complete(f, 'A'), lambda: lab.submit(f, 'B', 1),
                   lambda: lab.acquire(2), lambda: lab.release_ownership(f)]:
        with pytest.raises(ContractError):
            action()
    assert not f.returned


def test_color_capabilities_are_per_output_and_metadata_gates_independent():
    lab = Lab(); hdr = ('fp16', 'hdr', 'premultiplied')
    lab.outputs['A'].capabilities.add(hdr)
    assert lab.choose_color('A', hdr) == hdr
    assert lab.choose_color('B', hdr) == ('rgba8', 'sdr', 'opaque')
    assert lab.hdr_metadata_allowed('A', True, True, True)
    for flags in [(False, True, True), (True, False, True), (True, True, False)]:
        assert not lab.hdr_metadata_allowed('A', *flags)
    assert not lab.hdr_metadata_allowed('B', True, True, True)
    lab.outputs['A'].capabilities.remove(hdr)
    assert lab.choose_color('A', hdr) == ('rgba8', 'sdr', 'opaque')
    lab.outputs['B'].capabilities.clear()
    with pytest.raises(ContractError):
        lab.choose_color('B', hdr)


@pytest.mark.parametrize('gray',[0.0,0.18,0.5,1.0])
@pytest.mark.parametrize('alpha',[0.0,0.5,1.0])
def test_fixed_linear_gray_alpha_source_over_reference(gray,alpha):
    from media_surface_lab import premultiply, source_over
    # Thresholds fixed before outputs: CPU float 1e-6, 8-bit quantization 1/255.
    foreground=(gray,)*3; background=(0.25,)*3
    rgb,out_alpha=source_over(premultiply(foreground,alpha),alpha,background,1)
    expected=gray*alpha+0.25*(1-alpha)
    assert all(abs(c-expected)<=1e-6 for c in rgb)
    assert abs(out_alpha-1)<=1e-6
    assert all(abs(round(c*255)/255-expected)<=1/255 for c in rgb)


def test_double_premultiply_negative_control_and_primary_edges():
    from media_surface_lab import premultiply,source_over
    source=(1.0,0.0,0.0); alpha=0.5
    correct,_=source_over(premultiply(source,alpha),alpha,(0,0,1),1)
    wrong,_=source_over(premultiply(premultiply(source,alpha),alpha),alpha,(0,0,1),1)
    assert correct == (0.5,0,0.5)
    assert abs(wrong[0]-correct[0])>1/255  # Deliberate mutant must be detected.
    assert source_over((0,0,0),0,(0,1,0),1)==((0,1,0),1)
    assert source_over((1,0,0),1,(0,1,0),1)==((1,0,0),1)


def test_new_surface_requires_fresh_generation_bound_capability_query():
    lab=Lab(); hdr=('fp16','hdr','premultiplied')
    lab.update_capabilities('A',1,{hdr,('rgba8','sdr','opaque')})
    lab.destroy_output('A',1,True);lab.recreate_output('A')
    with pytest.raises(ContractError):
        lab.choose_color('A',hdr)
    with pytest.raises(ContractError):
        lab.update_capabilities('A',1,{hdr})
    lab.update_capabilities('A',2,{('rgba8','sdr','opaque')})
    assert lab.choose_color('A',hdr)==('rgba8','sdr','opaque')
