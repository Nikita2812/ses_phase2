"""
Quick test script to verify CLL system imports work correctly
"""

import sys

def test_imports():
    """Test all CLL component imports"""
    print("Testing CLL System Imports...\n")

    try:
        print("1. Testing Pydantic models...")
        from app.schemas.learning.models import (
            PreferenceType,
            UserPreferenceResponse,
            CorrectionResponse,
            PreferenceApplicationResult
        )
        print("   ✓ Pydantic models imported successfully")

        print("\n2. Testing PreferenceExtractor...")
        from app.services.learning.preference_extractor import PreferenceExtractor
        extractor = PreferenceExtractor()
        print("   ✓ PreferenceExtractor initialized successfully")

        print("\n3. Testing PreferenceManager...")
        from app.services.learning.preference_manager import PreferenceManager
        manager = PreferenceManager()
        print("   ✓ PreferenceManager initialized successfully")

        print("\n4. Testing CorrectionLearner...")
        from app.services.learning.correction_learner import CorrectionLearner
        learner = CorrectionLearner()
        print("   ✓ CorrectionLearner initialized successfully")

        print("\n5. Testing CLLChatIntegration...")
        from app.chat.cll_integration import CLLChatIntegration
        cll = CLLChatIntegration()
        print("   ✓ CLLChatIntegration initialized successfully")

        print("\n6. Testing API routes...")
        from app.api.learning_routes import learning_router
        print(f"   ✓ Learning router with {len(learning_router.routes)} routes")

        print("\n7. Testing Enhanced Chat integration...")
        from app.chat.enhanced_agent import EnhancedConversationalAgent
        agent = EnhancedConversationalAgent(enable_cll=True)
        print("   ✓ Enhanced Chat agent with CLL enabled")

        print("\n" + "="*60)
        print("✅ ALL IMPORTS SUCCESSFUL!")
        print("="*60)
        print("\nThe CLL system is properly configured and ready to use.")
        print("\nNext steps:")
        print("  1. Initialize database: psql -U postgres -d csa_db < init_continuous_learning.sql")
        print("  2. Start server: python main.py")
        print("  3. Test endpoints: http://localhost:8000/docs")

        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
