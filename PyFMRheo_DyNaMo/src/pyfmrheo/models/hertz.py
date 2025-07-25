import numpy as np
from lmfit import Model, Parameters

from .correction_factors import (
    bec_dimitriadis_paraboloid_bonded, bec_dimitriadis_paraboloid_not_bonded, 
    bec_gavara_cone, bec_managuli_cone, bec_garcia_garcia, sphere_approx_kontomaris
)

from .geom_coeffs import get_coeff

class HertzModel:
    # Model abstract class
    def __init__(self, ind_geom, tip_param, correction_model=None) -> None:
        # Tip geomtry params
        self.ind_geom = ind_geom         # No units
        self.tip_parameter = tip_param   # If radius units is meters, If half angle units is degrees
        self.correction_model = correction_model
        self.fit_method = 'leastsq' #leastsq is the default, Least-Squares minimization, using Trust Region Reflective method
        # Compiutation params
        self.fit_hline_flag = False
        self.apply_correction_flag = False
        # Model params #####################
        self.n_params = None
        # Contact point
        self.delta0 = 0
        self.delta0_init = 0
        self.delta0_min = -np.inf
        self.delta0_max = np.inf
        # Apparent Young's Modulus
        self.E0 = 1000
        self.E0_init = 1000
        self.E0_min = 0
        self.E0_max = np.inf
        # Contact force
        self.f0 = 0
        self.f0_init = 0
        self.f0_min = -np.inf
        self.f0_max = np.inf
        # Baseline slope
        self.slope = None
        self.slope_init = 0
        self.slope_min = -np.inf
        self.slope_max = np.inf
        # Poisson ratio
        self.poisson_ratio = 0.5
        # Sample height
        self.sample_height = None
        # Goodness of fit metrics
        self.MAE = None
        self.SE = None
        self.MSE = None
        self.RMSE = None
        self.Rsquared = None
        self.chisq = None
        self.redchi = None
        #this is to store the max indentation of a fitted force curve
        self.max_ind = None
        #this is to store the POC initial estimate
        self.z_c = None
        #this is to store the Z height at setpoint in m
        self.z_at_setpoint = None

    
    def get_correction_coeffs(self, sample_height, indentation):
        correction_params = [sample_height, (indentation - self.delta0), self.ind_geom, self.tip_parameter]
        if self.correction_model == 'dimitriadis_paraboloid_bonded':
            self.poisson_ratio = 0.5
            return bec_dimitriadis_paraboloid_bonded(*correction_params)
        elif self.correction_model == 'dimitriadis_paraboloid_not_bonded':
            self.poisson_ratio = 0.5
            return bec_dimitriadis_paraboloid_not_bonded(*correction_params)
        elif self.correction_model == 'gavara_cone':
            return bec_gavara_cone(*correction_params)
        elif self.correction_model == 'managuli_cone':
            return bec_managuli_cone(*correction_params)
        elif self.correction_model == 'garcia_garcia':
            self.poisson_ratio = 0.5
            return bec_garcia_garcia(*correction_params)
        elif self.correction_model == 'kontomaris':
            return sphere_approx_kontomaris(*correction_params)
        else:
            # TO DO: Implement custom exception
            raise Exception('Correction model not implemented')
    
    def build_params(self):
        params = Parameters()
        params.add('delta0', value=self.delta0_init, min=self.delta0_min, max=self.delta0_max)
        params.add('E0', value=self.E0_init, min=self.E0_min, max=self.E0_max)
        params.add('f0', value=self.f0_init, min=self.f0_min, max=self.f0_max)
        if self.fit_hline_flag:
            params.add('slope', value=self.slope_init, min=self.slope_min, max=self.slope_max)
        return params

    def model(self, indentation, delta0, E0, f0, slope=None, sample_height=None):
        # Define output array
        force = np.zeros(indentation.shape)
        
        # Get indenter shape coefficient and exponent
        coeff, n = get_coeff(self.ind_geom, self.tip_parameter, self.poisson_ratio)
        # Get bottom effect correction coefficients
        if self.correction_model and self.correction_model == 'kontomaris':
            correction_coeffs = self.get_correction_coeffs(None, indentation)
        elif self.correction_model and sample_height:
            correction_coeffs = self.get_correction_coeffs(sample_height, indentation)
        else:
            correction_coeffs = np.ones(indentation.shape)
        # Compute the force using Hertz model
        non_contact_mask = indentation < delta0
        contact_mask = ~non_contact_mask

        # Non-contact part
        if self.fit_hline_flag:
            # Fit a line on the non contact part
            force[non_contact_mask] = (indentation[non_contact_mask] - delta0) * slope + f0
        else:
            # Assign f0 as force value
            force[non_contact_mask] = f0

        # Contact part
        # Fit Hertz model on the contact part
        # F = F0 * Correction Coefficient
        force[contact_mask] = (
            coeff * correction_coeffs[contact_mask] * E0 * np.power((indentation[contact_mask] - delta0), n) + f0
        )

        return force

    def fit(self, indentation, force, sample_height=None):
        # If sample height is given, assign sample height
        #self.run_fit_ident = indentation;self.run_fit_force = force;self.sample_height = sample_height
        
        
        coeff, n = get_coeff(self.ind_geom, self.tip_parameter, self.poisson_ratio)
        self.E0_init = np.max(force) / coeff / np.max(indentation) ** n
        # Param order:
        # delta0, E0, f0, slope
        if self.fit_hline_flag:
            hertzmodel =\
             lambda indentation, delta0, E0, f0, slope: self.model(indentation, delta0, E0, f0, slope, self.sample_height)
        else:
            hertzmodel =\
             lambda indentation, delta0, E0, f0: self.model(indentation, delta0, E0, f0, self.slope, self.sample_height)
        
        hertzmodelfit = Model(hertzmodel)
        
        # Define free params
        params = self.build_params()
        
        # Do fit
        self.n_params = len(hertzmodelfit.param_names)
        result_hertz = hertzmodelfit.fit(force, params, indentation=indentation, method=self.fit_method)

        # Assign fit results to model params
        self.delta0 = result_hertz.best_values['delta0']
        self.E0 = result_hertz.best_values['E0']
        self.f0 = result_hertz.best_values['f0']
        if self.fit_hline_flag:
            self.slope = result_hertz.best_values['slope']
        
        modelPredictions = self.eval(indentation, sample_height)

        absError = modelPredictions - force

        self.MAE = np.mean(absError) # mean absolute error
        self.SE = np.square(absError) # squared errors
        self.MSE = np.mean(self.SE) # mean squared errors
        self.RMSE = np.sqrt(self.MSE) # Root Mean Squared Error, RMSE
        self.Rsquared = 1.0 - (np.var(absError) / np.var(force))
        
        # Get goodness of fit params
        self.chisq = self.get_chisq(indentation, force, sample_height)
        self.redchi = self.get_red_chisq(indentation, force, sample_height)

    def eval(self, indentation, sample_height=None):
        return self.model(indentation, self.delta0, self.E0, self.f0, self.slope, sample_height)
    
    def get_residuals(self, indentation, force,  sample_height=None):
        return force - self.eval(indentation, sample_height)

    def get_chisq(self, indentation, force, sample_height=None):
        
        #residuals = self.get_residuals(indentation, force, sample_height)
        # Only calculate where force is not zero
        #weighted_res = (residuals[force != 0] ** 2) / force[force != 0]
        # and getting a sum post filtering out non-finite values (e.g., NaN, inf)
        #return np.sum(weighted_res[np.isfinite(weighted_res)])
        
        a = (self.get_residuals(indentation, force, sample_height)**2/force)

        return np.sum(a[np.isfinite(a)])
    
    def get_red_chisq(self, indentation, force, sample_height=None):
        return self.get_chisq(indentation, force, sample_height) / self.n_params
    
    def fit_report(self):
        print(f"""
        # Fit parameters
        Indenter shape: {self.ind_geom}\n
        Tip paraneter: {self.tip_parameter}\n
        Correction Model: {self.correction_model}\n
        Number of free parameters: {self.n_params}\n
        delta0: {self.delta0}\n
        E0: {self.E0}\n
        f0: {self.f0}\n
        slope: {self.slope}\n
        # Fit metrics
        MAE: {self.MAE}\n
        MSE: {self.MSE}\n
        RMSE: {self.RMSE}\n
        Rsq: {self.Rsquared}\n
        Chisq: {self.chisq}\n
        RedChisq: {self.redchi}\n
        """
        )