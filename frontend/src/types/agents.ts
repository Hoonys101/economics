export interface AgentBasicDTO {
    id: number;
    type: string;
    wealth: number;
    income: number;
    expense: number;
}

export interface AgentDetailDTO extends AgentBasicDTO {
    is_active: boolean;
    // Household
    age?: number;
    needs?: Record<string, number>;
    inventory?: Record<string, number>;
    employer_id?: number;
    current_wage?: number;
    // Firm
    sector?: string;
    employees_count?: number;
    production?: number;
    revenue_this_turn?: Record<string, number>;
    expenses_this_tick?: Record<string, number>;
}
