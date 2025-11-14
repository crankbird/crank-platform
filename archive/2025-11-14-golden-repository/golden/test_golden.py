#!/usr/bin/env python3
"""
Golden Repository Health Check

Tests that the philosophical analyzer and integration pipeline work correctly.
Now includes validation of the new MASTER-ZETTEL-VAULT organization.
"""

import os
import sys
from pathlib import Path

# Add the philosophical-analyzer directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
analyzer_dir = os.path.join(current_dir, 'philosophical-analyzer')
sys.path.insert(0, analyzer_dir)

        test_content = """

        The network is more important than the nodes. When we build

        crank-mesh architectures, the value emerges from connections

        between services, not individual capabilities.def test_basic_functionality():

        """

        def test_basic_functionality():    """Test that the core analyzer functionality works."""

        analysis = analyzer.analyze_content("Network Test", test_content)

            """Test that the core analyzer functionality works."""    try:

        print("🧠 Philosophical Analyzer Test:")

        print(f"   NET marker detected: {analysis.primary_markers['NET']:.2f}")    try:        import philosophical_analyzer

        print(f"   Coherence score: {analysis.coherence_score:.2f}/5.0")

                import philosophical_analyzer        analyzer = philosophical_analyzer.PhilosophicalAnalyzer()

        readiness = analyzer.assess_readiness(analysis)

        print(f"   Readiness assessment: {readiness}")        analyzer = philosophical_analyzer.PhilosophicalAnalyzer()        

        

        # Verify NET marker was detected (should be > 0 for network content)        analyzer = PhilosophicalAnalyzer()

        assert analysis.primary_markers["NET"] > 0, "NET marker not detected"

        print("   ✅ Philosophical analyzer working correctly!")        # Test with Richard Martin style content        

        return True

                test_content = """        # Test with some Richard Martin style content

    except ImportError as e:

        print(f"   ❌ Import error: {e}")        The network is more important than the nodes. When we build        test_content = """

        return False

    except Exception as e:        crank-mesh architectures, the value emerges from connections        The network is more important than the nodes. When we build crank-mesh architectures,

        print(f"   ❌ Test error: {e}")

        return False        between services, not individual capabilities.        the value emerges from the connections between services, not from individual service capabilities.



        """        Each edge node coordinates autonomously while the central authority becomes unnecessary.

def test_content_availability():

    """Test that key content is available."""        """

    required_paths = [

        "zettels/curated-collection",        analysis = analyzer.analyze_content("Test", test_content)        

        "zettels/meta-analysis", 

        "zettels/personas",        analysis = analyzer.analyze_content("Test Network Thinking", test_content)

        "zettels/philosophical-insights",

        "integration-scripts",        print("🧠 Golden Repository Test Results:")        

        "semantic-config",

        "gherkins",        print(f"   Primary markers: {analysis.primary_markers}")        print("🧠 Golden Repository Test Results:")

        "coordination-docs"

    ]        print(f"   Coherence score: {analysis.coherence_score:.2f}/5.0")        print(f"   Primary markers: {analysis.primary_markers}")

    

    print("📁 Content Availability Test:")        print(f"   Coherence score: {analysis.coherence_score:.2f}/5.0")

    all_present = True

            readiness = analyzer.assess_readiness(analysis)        print(f"   Detected patterns: {analysis.detected_patterns}")

    for path in required_paths:

        full_path = current_dir / path        print(f"   Readiness: {readiness}")        

        if full_path.exists():

            if full_path.is_dir():        readiness = analyzer.assess_readiness(analysis)

                file_count = len(list(full_path.glob("*")))

                print(f"   ✅ {path}/ ({file_count} items)")        if analysis.coherence_score > 0:        print(f"   Readiness: {readiness}")

            else:

                print(f"   ✅ {path}")            print("✅ SUCCESS: Philosophical analyzer working!")        

        else:

            print(f"   ❌ Missing: {path}")            return True        if analysis.coherence_score > 0:

            all_present = False

            else:            print("✅ SUCCESS: Philosophical analyzer working correctly!")

    return all_present

            print("⚠️  WARNING: Low coherence - may need tuning")            return True



def test_key_files():            return False        else:

    """Test that critical files are present."""

    key_files = [            print("⚠️  WARNING: Low coherence score - may need pattern tuning")

        "zettels/philosophical-insights/master_MASTER-ZETTEL_Intelligence-Is-Situated.md",

        "zettels/meta-analysis/CONVERGENCE_SYNTHESIS_FINAL.md",     except ImportError as e:            return False

        "zettels/personas/sonnet_zk20251112-013_persona-recognition-tools.md",

        "philosophical-analyzer/philosophical_analyzer.py",        print(f"❌ IMPORT ERROR: {e}")            

        "integration-scripts/extract-gherkins.py",

        "coordination-docs/PLATFORM_GHERKINS.md"        return False    except ImportError as e:

    ]

        except Exception as e:        print(f"❌ IMPORT ERROR: {e}")

    print("📄 Key Files Test:")

    all_present = True        print(f"❌ ERROR: {e}")        return False

    

    for file_path in key_files:        return False    except Exception as e:

        full_path = current_dir / file_path

        if full_path.exists():        print(f"❌ ERROR: {e}")

            size = full_path.stat().st_size

            print(f"   ✅ {file_path} ({size} bytes)")        return False

        else:

            print(f"   ❌ Missing: {file_path}")if __name__ == "__main__":

            all_present = False

        success = test_basic_functionality()if __name__ == "__main__":

    return all_present

    sys.exit(0 if success else 1)    success = test_basic_functionality()

    sys.exit(0 if success else 1)
def main():
    """Run all health checks."""
    print("🚀 Golden Repository Health Check\n")
    
    tests = [
        ("Content Availability", test_content_availability),
        ("Key Files", test_key_files),
        ("Philosophical Analyzer", test_philosophical_analyzer)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n=== {test_name} ===")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("📊 HEALTH CHECK SUMMARY:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Golden repository is healthy and ready for deployment!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())