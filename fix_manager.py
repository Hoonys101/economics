import re

with open("modules/lifecycle/manager.py", "r") as f:
    content = f.read()

new_content = content.replace("    def register_household(self, dto: AgentRegistrationDTO) -> AgentID:\n        # Same atomic logic\n        pass", """    def register_household(self, dto: AgentRegistrationDTO) -> AgentID:
        try:
            new_id = self._next_id
            self._next_id += 1

            household_entity = self.household_factory.create(new_id, dto) if self.household_factory else None

            if not household_entity:
                raise AgentRegistrationException("Household factory not provided or failed.")

            self.registry.register(household_entity)

            cash_amount = dto.initial_assets.get("cash", 0)
            self.ledger.record_monetary_expansion(cash_amount, "HOUSEHOLD_REGISTRATION")

            self.logger.info(f"Household {new_id} registered atomically.")
            return new_id

        except Exception as e:
            self.logger.error(f"Failed to register household: {e}")
            raise AgentRegistrationException(str(e))""")

new_content = new_content.replace("""    def process_starvation(self, household_id: AgentID, current_tick: int) -> None:
        agent = self.registry.get_agent(household_id)
        if not agent:
            return

        # Inspect needs ...
        # if health drops to 0 -> deactivate
        pass""", """    def process_starvation(self, household_id: AgentID, current_tick: int) -> None:
        agent = self.registry.get_agent(household_id)
        if not agent:
            return

        if hasattr(agent, "needs"):
            survival = agent.needs.get("survival", 100.0)
            if survival <= 0:
                self.deactivate_agent(household_id, LifecycleEventType.STARVED)""")

with open("modules/lifecycle/manager.py", "w") as f:
    f.write(new_content)
