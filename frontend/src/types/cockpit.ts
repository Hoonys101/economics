export type CockpitCommandType =
    | "PAUSE"
    | "RESUME"
    | "STEP"
    | "SET_BASE_RATE"
    | "SET_TAX_RATE";

export interface SetBaseRatePayload {
    rate: number;
}

export interface SetTaxRatePayload {
    tax_type: "corporate" | "income";
    rate: number;
}

export type CockpitPayload = SetBaseRatePayload | SetTaxRatePayload | Record<string, unknown>;

export interface CockpitCommand {
    type: CockpitCommandType;
    payload: CockpitPayload;
}
