import type { DurationCalculation } from "./reviewSuggestionApi";

const number = (value: number, digits = 2) => value.toLocaleString("en-PH", { maximumFractionDigits: digits });

export function CalculationExplanation({ calculation, registrationProxy, submissionProxy = false, formatTime }: {
  calculation?: DurationCalculation | null;
  registrationProxy: boolean;
  submissionProxy?: boolean;
  formatTime: (value: string) => string;
}) {
  const median = calculation?.quantiles.find(row => row.quantile === .5);
  if (!calculation || !median) return <p className="text-xs text-slate-500">Calculation steps are not available for this response. The estimate above remains unchanged.</p>;
  return <div aria-label="Calculation walkthrough" className="space-y-4">
    <h4 className="font-semibold text-slate-900">How this estimate is calculated</h4>
    <ol className="space-y-4">
      <li className="space-y-1">
        <p className="font-medium text-slate-900">1. Choose the starting time</p>
        <p>{submissionProxy ? "Citizen report submitted" : registrationProxy ? "Admin registration" : "First recorded flooding"}: <strong>{formatTime(calculation.reference_at)} (PHT)</strong>.</p>
        {registrationProxy && <p className="text-xs text-amber-800">This is a recording-time proxy. We do not know when flooding actually began.</p>}
        <p className="text-xs">Forecast anchored at {formatTime(calculation.prediction_as_of_at)} (PHT). At that anchor, {number(calculation.elapsed_minutes)} minutes had elapsed from the starting time, assuming uninterrupted flooding. Refreshing this view does not move the anchor.</p>
      </li>
      <li className="space-y-2">
        <p className="font-medium text-slate-900">2. Apply the learned duration pattern</p>
        <p>The model fits a spread of reported subsidence durations from historical Pasig records. It returns an earlier estimate, a middle estimate and a later estimate.</p>
        <p className="font-mono text-xs leading-6 break-words">ln(T) = μ + σ × Z</p>
        <p className="text-xs">T is total duration in minutes. μ = {number(calculation.log_duration_location, 6)} is the fitted log-duration centre; σ = {number(calculation.log_duration_scale, 6)} is its spread. Z selects a point in that spread. The middle estimate is the model’s 50th percentile, not a guaranteed clearing time.</p>
        <p className="text-xs">For this forecast, the middle normal score Z is {number(median.normal_score, 6)}.</p>
        <p className="font-mono text-xs leading-6 break-words">Total duration = exp({number(calculation.log_duration_location, 6)} + {number(calculation.log_duration_scale, 6)} × {number(median.normal_score, 6)}) ≈ {number(median.total_minutes)} min</p>
        <p className="font-mono text-xs leading-6 break-words">Remaining at anchor = {number(median.total_minutes)} − {number(calculation.elapsed_minutes)} ≈ {number(median.remaining_minutes)} min</p>
      </li>
      <li className="space-y-2">
        <p className="font-medium text-slate-900">3. Turn the duration into a date</p>
        <p className="font-medium text-slate-900">{formatTime(calculation.prediction_as_of_at)} + about {median.remaining_duration_display} ≈ {formatTime(median.estimated_reported_subsidence_at)} (PHT)</p>
        <p className="text-xs">The formula uses full precision. The values shown here are rounded. This duration is measured from the forecast anchor, not from the time you open this window.</p>
        <dl className="space-y-2">
          {calculation.quantiles.map(row => <div key={row.quantile} className="grid gap-1 sm:grid-cols-[10rem_1fr]">
            <dt className="font-medium">{row.quantile === .1 ? "Earlier · 10th percentile" : row.quantile === .5 ? "Middle · 50th percentile" : "Later · 90th percentile"}</dt>
            <dd>{formatTime(row.estimated_reported_subsidence_at)} (PHT)</dd>
          </div>)}
        </dl>
        <p className="text-xs">The earlier-to-later interval contains the middle 80% of this assumed model distribution. It does not mean the forecast is proven 80% accurate or that the road is dry.</p>
      </li>
    </ol>
    <details className="text-xs">
      <summary className="min-h-11 cursor-pointer py-3 font-medium text-blue-700">Elapsed-time formula</summary>
      <div className="space-y-2 pt-2 leading-5">
        <p>When time has already elapsed at the anchor, the calculation conditions on flooding continuing beyond that age.</p>
        <p className="font-mono break-words">p = F(a) + q × (1 − F(a))</p>
        <p className="font-mono break-words">Z = Φ⁻¹(p); T = exp(μ + σ × Z)</p>
        <p>Here a = {number(calculation.elapsed_minutes)} minutes, F(a) = {number(calculation.probability_before_anchor, 6)}, q = 0.5 and p = {number(median.adjusted_probability, 6)} for the middle estimate. F(a) is the fitted probability of a reported subsidence by age a; Φ⁻¹ turns a probability into a normal score. At age zero, F(a) is zero and the middle score is zero.</p>
      </div>
    </details>
  </div>;
}
