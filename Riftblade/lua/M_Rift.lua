function RBRESC(effect, target)
	local caster = EEex_GameObject_Get(effect.m_sourceId)
	if not caster or not caster.m_pArea or not target.m_pArea then
		return
	end

	local x, y = EEex_Area_GetNearestOpenPosition(
		target.m_pArea,
		caster.m_pos.x,
		caster.m_pos.y,
		true
	)
	if not x or not y then
		return
	end

	EEex_Action_QueueResponseStringOnAIBase(
		string.format("JumpToPoint([%d.%d])", x, y),
		target
	)
end
