-- @summary: Returns button data for a spell, using the provided itemType.
--
-- @param { spellResRef / type=string }: The spell resource reference.
-- @param { spellHeader / type=Spell_Header_st }: The spell header structure.
-- @param { spellAbility / type=Spell_ability_st }: The spell ability structure.
-- @param { itemType / type=number }: The item type to assign to the ability ID.
--
-- @return { usertype=CButtonData }: The created button data.
function EEex_Actionbar_GetSpellButtonDataWithItemType(spellResRef, spellHeader, spellAbility, itemType)
	local buttonData = EEex_NewUD("CButtonData")
	buttonData.m_icon:set(spellAbility.quickSlotIcon:get())
	buttonData.m_name = spellHeader.genericName
	buttonData.m_launcherIcon:set("")
	buttonData.m_launcherName = 0xFFFFFFFF
	buttonData.m_count = 1
	local abilityId = buttonData.m_abilityId
	abilityId.m_itemType = itemType or 3
	abilityId.m_itemNum = -1
	abilityId.m_abilityNum = -1
	abilityId.m_res:set(spellResRef)
	abilityId.m_targetType = spellAbility.actionType
	abilityId.m_targetCount = spellAbility.actionCount
	abilityId.m_toolTip = spellHeader.genericName
	buttonData.m_bDisabled = false
	buttonData.m_bDisplayCount = 0
	return buttonData
end

-- @summary: Wraps a spell iterator and builds a spell button data iterator using a custom itemType.
--
-- @param { spellIterator / type=function }: Iterator returning <string spellResRef, Spell_Header_st spellHeader, Spell_ability_st spellAbility>.
-- @param { itemType / type=number }: Item type to set on each button's ability ID.
--
-- @return { type=function }: Iterator returning <CButtonData>.
function EEex_Actionbar_GetSpellButtonDataIteratorWithItemType(spellIterator, itemType)
	return EEex_Utility_ApplyItr(spellIterator,
		function(spellResRef, spellHeader, spellAbility)
			return EEex_Actionbar_GetSpellButtonDataWithItemType(spellResRef, spellHeader, spellAbility, itemType)
		end
	)
end
EEex_Actionbar_GetSpellButtonDataItrWithItemType = EEex_Actionbar_GetSpellButtonDataIteratorWithItemType

-- @summary: Wraps a spell iterator and filters out opcode #214 excluded spells, then builds button data with a custom itemType.
--
-- @param { spellIterator / type=function }: Iterator returning <string spellResRef, Spell_Header_st spellHeader, Spell_ability_st spellAbility>.
-- @param { itemType / type=number }: Item type to set on each button's ability ID.
--
-- @return { type=function }: Iterator returning <CButtonData>.
function EEex_Actionbar_GetOp214ButtonDataIteratorWithItemType(spellIterator, itemType)
	return EEex_Actionbar_GetSpellButtonDataItrWithItemType(EEex_Utility_FilterItr(spellIterator,
		function(spellResRef, spellHeader, spellAbility)
			return spellResRef ~= "SPWI110" and spellResRef ~= "SPWI124"
		end
	), itemType)
end
EEex_Actionbar_GetOp214ButtonDataItrWithItemType = EEex_Actionbar_GetOp214ButtonDataIteratorWithItemType

-- @summary: Main spell to be used by opcode #214, get all memorized spells that can be cast by the mage and then cast the selected one instantly
function CHQUICK(effect, sprite)
	local memorizedSpells = sprite.m_memorizedSpellsMage

    return EEex_Actionbar_GetOp214ButtonDataItrWithItemType(EEex_Utility_SelectItr(3, EEex_Utility_FilterItr(        
        sprite:getKnownMageSpellsWithAbilityIterator(1, 9),
        function(spellLevel, knownSpellIndex, spellResRef, spellHeader, spellAbility)
			local memList = memorizedSpells:getReference(spellLevel)
			local canCast = false
			
			EEex_Utility_IterateCPtrList(memList, function(memInstance)
				local memInstanceSpellId = memInstance.m_spellId:get()
				
				if memInstanceSpellId == spellResRef and memInstance.m_flags == 1 then
					canCast = true
					return true
				end
			end)
			
			return canCast			
        end
    )), 5)
end

