def get_params(params, method):
    # Create dictionary to hold parameters
    param_dict = {}
    
    # Define general parameters
    param_dict['compute_all_curves'] = params.child('General Options').child('Compute All Curves').value()
    param_dict['method'] = method
    analysis_params = params.child('Analysis Params')
    param_dict['height_channel'] = analysis_params.child('Height Channel').value()
    param_dict['def_sens'] = analysis_params.child('Deflection Sensitivity').value() / 1e9
    param_dict['k'] = analysis_params.child('Spring Constant').value()
    if method in ("PiezoChar", "VDrag", "Microrheo", "MicrorheoSine"):
        param_dict['max_freq'] = analysis_params.child('Max Frequency').value()
    if method in ("VDrag", "Microrheo", "MicrorheoSine"):
        correction_params = params.child('Correction Params')
        param_dict['corr_amp'] = correction_params.child('Correct Amplitude').value()
    if method in ("PiezoChar", "VDrag"):
        return param_dict
    if method in ("Microrheo", "MicrorheoSine"):
        param_dict['bcoef'] = analysis_params.child('B Coef').value()
        param_dict['wc'] = analysis_params.child('Working Indentation').value() / 1e9 # nm
    param_dict['contact_model'] = analysis_params.child('Contact Model').value()
    if param_dict['contact_model'] == "paraboloid":
        param_dict['tip_param'] = analysis_params.child('Tip Radius').value() / 1e9 # nm
    elif param_dict['contact_model'] in ("cone", "pyramid"):
        param_dict['tip_param'] = analysis_params.child('Tip Angle').value()
    
    param_dict['curve_seg'] = analysis_params.child('Curve Segment').value()
    param_dict['correct_tilt'] = analysis_params.child('Correct Tilt').value()
    param_dict['offset_type'] = analysis_params.child('Offset Type').value()
    if param_dict['offset_type'] == 'percentage':
        param_dict['min_offset'] = analysis_params.child('Perc. Min Offset').value() / 1e2
        param_dict['max_offset'] = analysis_params.child('Perc. Max Offset').value() / 1e2
    else:
        param_dict['min_offset'] = analysis_params.child('Abs. Min Offset').value() / 1e9 #nm
        param_dict['max_offset'] = analysis_params.child('Abs. Max Offset').value() / 1e9 #nm
    
    # HertzFit specific parameters
    if method  in ("HertzFit", "Microrheo", "MicrorheoSine"):
        hertz_params = params.child('Hertz Fit Params')
        param_dict['poisson'] = hertz_params.child('Poisson Ratio').value()
        param_dict['poc_method'] = hertz_params.child('PoC Method').value()
        param_dict['poc_win'] = hertz_params.child('PoC Window').value() / 1e9 #nm
        param_dict['sigma'] = hertz_params.child('Sigma').value()
        param_dict['downsample_flag'] = hertz_params.child('Downsample Signal').value()
        param_dict['pts_downsample'] = hertz_params.child('Downsample Pts.').value()
        param_dict['auto_init_E0'] = hertz_params.child('Auto Init E0').value()
        param_dict['E0'] = hertz_params.child('Init E0').value()
        param_dict['d0'] = hertz_params.child('Init d0').value() / 1e9 #nm
        param_dict['f0'] = hertz_params.child('Init f0').value() / 1e9 #nN
        param_dict['slope'] = hertz_params.child('Init Slope').value()
        param_dict['fit_range_type'] = hertz_params.child('Fit Range Type').value()
        param_dict['max_ind'] = hertz_params.child('Max Indentation').value() / 1e9 #nm
        param_dict['min_ind'] = hertz_params.child('Min Indentation').value() / 1e9 #nm
        param_dict['max_force'] = hertz_params.child('Max Force').value() / 1e9 #nN
        param_dict['min_force'] = hertz_params.child('Min Force').value() / 1e9 #nN
        param_dict['fit_line'] = hertz_params.child('Fit Line to non contact').value()
        param_dict['contact_offset'] = hertz_params.child('Contact Offset').value() / 1e6 #um

    # TingFit specific parameters
    elif method == "TingFit":
        # Define downsample for hertzfit flag
        # Decide how to handle this in the future:
        # - Allow user to downsample for hertz fit
        param_dict['downsample_flag'] = False
        # Define ting params
        ting_params = params.child('Ting Fit Params')
        param_dict['poisson'] = ting_params.child('Poisson Ratio').value()
        param_dict['poc_method'] = ting_params.child('PoC Method').value()
        param_dict['poc_win'] = ting_params.child('PoC Window').value() / 1e9 #nm
        param_dict['sigma'] = ting_params.child('Sigma').value()
        param_dict['max_ind'] = ting_params.child('Max Indentation').value() / 1e9 #nm
        param_dict['min_ind'] = ting_params.child('Min Indentation').value() / 1e9 #nm
        param_dict['max_force'] = ting_params.child('Max Force').value() / 1e9 #nN
        param_dict['min_force'] = ting_params.child('Min Force').value() / 1e9 #nN
        param_dict['fit_range_type'] = ting_params.child('Fit Range Type').value()
        param_dict['vdragcorr'] = ting_params.child('Correct Viscous Drag').value()
        param_dict['polyordr'] = ting_params.child('Poly. Order').value()
        param_dict['rampspeed'] = ting_params.child('Ramp Speed').value() / 1e6 #um/s
        param_dict['compute_v_flag'] = ting_params.child('Estimate V0t & V0r').value()
        param_dict['t0'] = ting_params.child('t0').value()
        param_dict['d0'] = ting_params.child('Init d0').value() / 1e9 #nm
        param_dict['slope'] = ting_params.child('Init Slope').value()
        param_dict['auto_init_E0'] = ting_params.child('Auto Init E0').value()
        param_dict['E0'] = ting_params.child('Init E0').value()
        param_dict['tc'] = ting_params.child('Init tc').value()
        param_dict['auto_init_betaE'] = ting_params.child('Auto Init  Fluid. Exp.').value()
        param_dict['fluid_exp'] = ting_params.child('Init Fluid. Exp.').value()
        param_dict['f0'] = ting_params.child('Init f0').value() / 1e9 #nN
        param_dict['vdrag'] = ting_params.child('Viscous Drag').value() / 1e3 #N/m·s
        param_dict['model_type'] = ting_params.child('Model Type').value()
        param_dict['smoothing_win'] = ting_params.child('Smoothing Window').value()
        param_dict['contact_offset'] = ting_params.child('Contact Offset').value() / 1e6 #um
        param_dict['slope'] = ting_params.child('Init Slope').value()
        param_dict['fit_line'] = ting_params.child('Fit Line to non contact').value()
        param_dict['pts_downsample'] = ting_params.child('Downsample Pts.').value()
    
    return param_dict